from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal
from .models import Quiz, Question, QuestionOption, QuizAttempt, Answer
from .forms import QuizForm, QuestionForm
from authentication.models import User
from studyplan.models import StudyPlan
import json


def require_login(view_func):
    """Custom decorator to check if user is logged in via session"""
    def wrapper(request, *args, **kwargs):
        if not request.session.get("app_user_id"):
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return wrapper


def update_user_rankings():
    """Update rankings for all users based on total_points"""
    users = User.objects.all().order_by('-total_points', 'id')
    
    for rank, user in enumerate(users, start=1):
        user.current_rank = rank
        user.save(update_fields=['current_rank'])


def get_quiz_list_url(quiz):
    """Helper function to build quiz_list URL with study_plan parameter if applicable"""
    if quiz and quiz.study_plan:
        return f"/quiz/?study_plan={quiz.study_plan.id}"
    return "/quiz/"


@require_login
def quiz_list(request):
    """Display all quizzes for the logged-in user including public quizzes from same categories"""
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    
    # Check if filtering by study plan
    study_plan_id = request.GET.get('study_plan')
    selected_study_plan = None
    
    if study_plan_id:
        try:
            selected_study_plan = StudyPlan.objects.get(id=study_plan_id, user=user)
            # Get quizzes for this specific study plan
            my_quizzes = Quiz.objects.filter(created_by=user, study_plan=selected_study_plan)
            
            # Available quizzes: AI-generated quizzes for this study plan + public quizzes from same category
            ai_quizzes = Quiz.objects.filter(study_plan=selected_study_plan, created_by=None)
            
            # Get public quizzes from other users with the same topic category
            public_quizzes = Quiz.objects.filter(
                is_public=True,
                status='published',
                study_plan__topic_category=selected_study_plan.topic_category
            ).exclude(created_by=user).exclude(created_by=None)
            
            study_plan_quizzes = list(ai_quizzes) + list(public_quizzes)
            
        except StudyPlan.DoesNotExist:
            my_quizzes = Quiz.objects.filter(created_by=user)
            study_plan_quizzes = Quiz.objects.filter(study_plan__user=user).exclude(created_by=user)
    else:
        # Get all quizzes created by user
        my_quizzes = Quiz.objects.filter(created_by=user)
        
        # Get all user's study plans to find relevant quizzes
        user_study_plans = StudyPlan.objects.filter(user=user)
        user_categories = user_study_plans.values_list('topic_category', flat=True).distinct()
        
        # Available quizzes: AI quizzes from user's study plans + public quizzes from same categories
        ai_quizzes = Quiz.objects.filter(study_plan__user=user, created_by=None)
        
        public_quizzes = Quiz.objects.filter(
            is_public=True,
            status='published',
            study_plan__topic_category__in=user_categories
        ).exclude(created_by=user).exclude(created_by=None)
        
        study_plan_quizzes = list(ai_quizzes) + list(public_quizzes)
    
    # For quizzes, check if user has taken them
    quiz_attempts = {}
    for quiz in study_plan_quizzes:
        # Track attempts for ALL quizzes (AI and user-created)
        has_taken = QuizAttempt.objects.filter(quiz=quiz, user=user, completed_at__isnull=False).exists()
        quiz_attempts[quiz.id] = has_taken
    
    return render(request, 'quiz/quiz_list.html', {
        'my_quizzes': my_quizzes,
        'study_plan_quizzes': study_plan_quizzes,
        'quiz_attempts': quiz_attempts,
        'selected_study_plan': selected_study_plan,
        'name': request.session.get("app_user_name", "User")
    })


@require_login
def create_quiz(request):
    """Create a new quiz"""
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    
    # Get study plan from URL parameter if provided
    study_plan_id = request.GET.get('study_plan')
    initial_study_plan = None
    if study_plan_id:
        try:
            initial_study_plan = StudyPlan.objects.get(id=study_plan_id, user=user)
        except StudyPlan.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.created_by = user
            quiz.status = 'draft'
            quiz.is_public = False  # Default to private/not public
            quiz.save()
            messages.success(request, f'Quiz "{quiz.title}" created! Now add questions.')
            url = reverse('add_question_custom', kwargs={'quiz_id': quiz.id})
            if quiz.study_plan:
                url += f'?study_plan={quiz.study_plan.id}'
            return redirect(url)
    else:
        # Pre-fill study plan if provided in URL
        if initial_study_plan:
            form = QuizForm(initial={'study_plan': initial_study_plan})
        else:
            form = QuizForm()
        # Filter study plans to only user's study plans
        form.fields['study_plan'].queryset = StudyPlan.objects.filter(user=user)
    
    return render(request, 'quiz/create_quiz.html', {
        'form': form,
        'selected_study_plan': initial_study_plan,
        'name': request.session.get("app_user_name", "User")
    })


@require_login
def add_question(request, quiz_id):
    """Add questions to a quiz"""
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    quiz = get_object_or_404(Quiz, id=quiz_id, created_by=user)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Create question
                question = form.save(commit=False)
                question.quiz = quiz
                question.order = quiz.questions.count() + 1
                question.save()
                
                # Create options A, B, C, D
                options_data = [
                    ('A', form.cleaned_data['option_a']),
                    ('B', form.cleaned_data['option_b']),
                    ('C', form.cleaned_data['option_c']),
                    ('D', form.cleaned_data['option_d']),
                ]
                
                correct_answer = form.cleaned_data['correct_answer']
                
                for idx, (letter, text) in enumerate(options_data):
                    QuestionOption.objects.create(
                        question=question,
                        option_text=text,
                        is_correct=(letter == correct_answer),
                        order=idx
                    )
                
                # Update quiz total questions
                quiz.total_questions = quiz.questions.count()
                quiz.save()
                
                messages.success(request, f'Question {question.order} added successfully!')
                
                # Check if user wants to add more questions
                if 'add_another' in request.POST:
                    url = reverse('add_question', kwargs={'quiz_id': quiz.id})
                    if quiz.study_plan:
                        url += f'?study_plan={quiz.study_plan.id}'
                    return redirect(url)
                else:
                    url = reverse('quiz_detail', kwargs={'quiz_id': quiz.id})
                    if quiz.study_plan:
                        url += f'?study_plan={quiz.study_plan.id}'
                    return redirect(url)
    else:
        form = QuestionForm()
    
    questions = quiz.questions.all()
    
    return render(request, 'quiz/add_question.html', {
        'form': form,
        'quiz': quiz,
        'questions': questions,
        'name': request.session.get("app_user_name", "User")
    })


@require_login
def add_question_custom(request, quiz_id):
    """Add custom questions with flexible options (Google Forms style)"""
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    quiz = get_object_or_404(Quiz, id=quiz_id, created_by=user)
    
    if request.method == 'POST':
        question_text = request.POST.get('question_text')
        question_type = request.POST.get('question_type', 'multiple_choice')
        explanation = request.POST.get('explanation', '')
        
        if not question_text:
            messages.error(request, 'Question text is required!')
            return redirect('add_question_custom', quiz_id=quiz.id)
        
        with transaction.atomic():
            # Create question
            question = Question.objects.create(
                quiz=quiz,
                question_text=question_text,
                question_type=question_type,
                explanation=explanation,
                order=quiz.questions.count() + 1
            )
            
            # Get all options from POST data
            option_keys = [key for key in request.POST.keys() if key.startswith('option_')]
            options_created = 0
            
            for option_key in option_keys:
                option_text = request.POST.get(option_key)
                if option_text:
                    # Extract option ID from key (e.g., "option_1" -> "1")
                    option_id = option_key.replace('option_', '')
                    
                    # Determine if this option is correct
                    is_correct = False
                    if question_type == 'checkboxes':
                        # Multiple correct answers possible
                        correct_options = request.POST.getlist('correct_option')
                        is_correct = option_id in correct_options
                    elif question_type == 'dropdown':
                        # Check dropdown select
                        dropdown_value = request.POST.get(f'correct_option_{option_id}', '0')
                        is_correct = dropdown_value == '1'
                    else:
                        # Single correct answer (multiple_choice)
                        correct_option = request.POST.get('correct_option')
                        is_correct = option_id == correct_option
                    
                    QuestionOption.objects.create(
                        question=question,
                        option_text=option_text,
                        is_correct=is_correct,
                        order=options_created
                    )
                    options_created += 1
            
            # Update quiz total questions
            quiz.total_questions = quiz.questions.count()
            quiz.save()
            
            messages.success(request, f'Question {question.order} added successfully!')
            
            # Check if user wants to add more questions
            if request.POST.get('action') == 'add_another':
                url = reverse('add_question_custom', kwargs={'quiz_id': quiz.id})
                if quiz.study_plan:
                    url += f'?study_plan={quiz.study_plan.id}'
                return redirect(url)
            else:
                url = reverse('quiz_detail', kwargs={'quiz_id': quiz.id})
                if quiz.study_plan:
                    url += f'?study_plan={quiz.study_plan.id}'
                return redirect(url)
    
    return render(request, 'quiz/add_question_custom.html', {
        'quiz': quiz,
        'name': request.session.get("app_user_name", "User")
    })


@require_login
def quiz_detail(request, quiz_id):
    """View quiz details and questions"""
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check if this is a view-only request (from admin)
    view_only = request.GET.get('view_only') == '1'
    
    # Check if user can access this quiz
    # AI-generated quizzes (created_by is None) cannot be edited or deleted
    can_edit = quiz.created_by == user
    is_ai_quiz = quiz.created_by is None
    is_other_user_quiz = quiz.created_by is not None and quiz.created_by != user
    
    # Get user's attempts
    attempts = QuizAttempt.objects.filter(quiz=quiz, user=user).order_by('-started_at')
    
    # Check if user has already taken quiz
    has_taken_quiz = attempts.filter(completed_at__isnull=False).exists()
    
    # For AI quizzes, redirect to take_quiz if not yet taken (unless view_only)
    if not view_only and is_ai_quiz and not has_taken_quiz:
        messages.info(request, 'Take the quiz first to see the details!')
        return redirect('take_quiz', quiz_id=quiz.id)
    
    # For other users' quizzes, redirect to take_quiz if not yet taken (unless view_only)
    if not view_only and is_other_user_quiz and not has_taken_quiz:
        messages.info(request, 'Take the quiz first to see the details!')
        return redirect('take_quiz', quiz_id=quiz.id)
    
    questions = quiz.questions.prefetch_related('options').all()
    
    return render(request, 'quiz/quiz_detail.html', {
        'quiz': quiz,
        'questions': questions,
        'can_edit': can_edit,
        'is_ai_quiz': is_ai_quiz,
        'is_other_user_quiz': is_other_user_quiz,
        'has_taken_quiz': has_taken_quiz,
        'attempts': attempts,
        'selected_study_plan': quiz.study_plan,
        'view_only': view_only,
        'name': request.session.get("app_user_name", "User")
    })


@require_login
def edit_question(request, question_id):
    """Edit a question"""
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    question = get_object_or_404(Question, id=question_id, quiz__created_by=user)
    
    # Get existing options
    options = list(question.options.order_by('order'))
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            with transaction.atomic():
                question = form.save()
                
                # Update options
                options_data = [
                    form.cleaned_data['option_a'],
                    form.cleaned_data['option_b'],
                    form.cleaned_data['option_c'],
                    form.cleaned_data['option_d'],
                ]
                
                correct_answer = form.cleaned_data['correct_answer']
                letters = ['A', 'B', 'C', 'D']
                
                for idx, (option, text) in enumerate(zip(options, options_data)):
                    option.option_text = text
                    option.is_correct = (letters[idx] == correct_answer)
                    option.save()
                
                messages.success(request, 'Question updated successfully!')
                url = reverse('quiz_detail', kwargs={'quiz_id': question.quiz.id})
                if question.quiz.study_plan:
                    url += f'?study_plan={question.quiz.study_plan.id}'
                return redirect(url)
    else:
        # Pre-fill form with existing data
        initial_data = {
            'option_a': options[0].option_text if len(options) > 0 else '',
            'option_b': options[1].option_text if len(options) > 1 else '',
            'option_c': options[2].option_text if len(options) > 2 else '',
            'option_d': options[3].option_text if len(options) > 3 else '',
            'correct_answer': next((chr(65 + i) for i, opt in enumerate(options) if opt.is_correct), 'A')
        }
        form = QuestionForm(instance=question, initial=initial_data)
    
    return render(request, 'quiz/edit_question.html', {
        'form': form,
        'question': question,
        'name': request.session.get("app_user_name", "User")
    })


@require_login
def delete_question(request, question_id):
    """Delete a question"""
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    question = get_object_or_404(Question, id=question_id, quiz__created_by=user)
    quiz = question.quiz
    
    if request.method == 'POST':
        question.delete()
        # Update quiz total questions
        quiz.total_questions = quiz.questions.count()
        quiz.save()
        messages.success(request, 'Question deleted successfully!')
        url = reverse('quiz_detail', kwargs={'quiz_id': quiz.id})
        if quiz.study_plan:
            url += f'?study_plan={quiz.study_plan.id}'
        return redirect(url)
    
    return render(request, 'quiz/delete_question.html', {
        'question': question,
        'name': request.session.get("app_user_name", "User")
    })


@require_login
def delete_quiz(request, quiz_id):
    """Delete a quiz (only drafts can be deleted)"""
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    quiz = get_object_or_404(Quiz, id=quiz_id, created_by=user)
    
    # Only allow deletion of draft quizzes
    if quiz.status != 'draft':
        messages.error(request, 'Only draft quizzes can be deleted!')
        return redirect('quiz_detail', quiz_id=quiz.id)
    
    if request.method == 'POST':
        study_plan_id = quiz.study_plan.id if quiz.study_plan else None
        quiz.delete()
        messages.success(request, 'Quiz deleted successfully!')
        if study_plan_id:
            return redirect(f'/quiz/?study_plan={study_plan_id}')
        return redirect('quiz_list')
    
    return redirect('quiz_detail', quiz_id=quiz.id)


@require_login
def publish_quiz(request, quiz_id):
    """Toggle quiz public/private status"""
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    quiz = get_object_or_404(Quiz, id=quiz_id, created_by=user)
    
    if quiz.questions.count() == 0:
        messages.error(request, 'Cannot make quiz public without questions!')
        url = reverse('quiz_detail', kwargs={'quiz_id': quiz.id})
        if quiz.study_plan:
            url += f'?study_plan={quiz.study_plan.id}'
        return redirect(url)
    
    # Toggle is_public status and publish the quiz
    quiz.is_public = not quiz.is_public
    
    if quiz.is_public:
        # Making public: publish the quiz
        quiz.status = 'published'
        messages.success(request, f'Quiz "{quiz.title}" is now public and published!')
    else:
        # Making private: keep it as draft
        quiz.status = 'draft'
        messages.success(request, f'Quiz "{quiz.title}" is now private!')
    
    quiz.save()
    url = reverse('quiz_detail', kwargs={'quiz_id': quiz.id})
    if quiz.study_plan:
        url += f'?study_plan={quiz.study_plan.id}'
    return redirect(url)


@require_login
def take_quiz(request, quiz_id):
    """Take a quiz"""
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check if quiz is published
    if quiz.status != 'published':
        messages.error(request, 'This quiz is not published yet!')
        if quiz.study_plan:
            return redirect(f'/quiz/?study_plan={quiz.study_plan.id}')
        return redirect('quiz_list')
    
    # Check completed attempts only (ignore incomplete/abandoned attempts)
    completed_attempts_count = QuizAttempt.objects.filter(
        quiz=quiz, 
        user=user, 
        completed_at__isnull=False
    ).count()
    
    # AI-generated quizzes (created_by is None) only allow one attempt
    if quiz.created_by is None and completed_attempts_count >= 1:
        messages.error(request, 'You have already completed this AI-generated quiz!')
        url = reverse('quiz_detail', kwargs={'quiz_id': quiz.id})
        if quiz.study_plan:
            url += f'?study_plan={quiz.study_plan.id}'
        return redirect(url)
    
    # User-created quizzes: check allow_review setting
    if quiz.created_by is not None and not quiz.allow_review and completed_attempts_count >= 1:
        messages.error(request, 'This quiz does not allow retakes!')
        url = reverse('quiz_detail', kwargs={'quiz_id': quiz.id})
        if quiz.study_plan:
            url += f'?study_plan={quiz.study_plan.id}'
        return redirect(url)
    
    # Create new attempt
    attempt = QuizAttempt.objects.create(
        quiz=quiz,
        user=user,
        study_plan=quiz.study_plan,
        attempt_number=completed_attempts_count + 1
    )
    
    questions = quiz.questions.prefetch_related('options').all()
    
    if quiz.shuffle_questions:
        questions = list(questions)
        import random
        random.shuffle(questions)
    
    # Check if it's an AI quiz
    is_ai_quiz = quiz.created_by is None
    
    return render(request, 'quiz/take_quiz.html', {
        'quiz': quiz,
        'attempt': attempt,
        'questions': questions,
        'is_ai_quiz': is_ai_quiz,
        'selected_study_plan': quiz.study_plan,
        'name': request.session.get("app_user_name", "User")
    })


@require_login
def submit_quiz(request, attempt_id):
    """Submit quiz answers and award points"""
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=user)
    
    if request.method == 'POST':
        with transaction.atomic():
            correct_count = 0
            total_questions = attempt.quiz.total_questions
            
            for question in attempt.quiz.questions.all():
                # Handle different question types
                if question.question_type == 'checkboxes':
                    # Multiple answers possible - get list of selected options
                    selected_option_ids = request.POST.getlist(f'question_{question.id}')
                    
                    if selected_option_ids:
                        # Get all correct option IDs for this question
                        correct_option_ids = set(
                            question.options.filter(is_correct=True).values_list('id', flat=True)
                        )
                        selected_ids_set = set(int(id) for id in selected_option_ids)
                        
                        # Check if selected options match correct options exactly
                        is_correct = selected_ids_set == correct_option_ids
                        
                        # Create answer records for each selected option
                        for option_id in selected_option_ids:
                            selected_option = QuestionOption.objects.get(id=option_id)
                            Answer.objects.create(
                                question=question,
                                attempt=attempt,
                                selected_option=selected_option,
                                is_correct=is_correct  # All or nothing for checkboxes
                            )
                        
                        if is_correct:
                            correct_count += 1
                else:
                    # Single answer (multiple_choice, dropdown, true_false)
                    selected_option_id = request.POST.get(f'question_{question.id}')
                    
                    if selected_option_id:
                        selected_option = QuestionOption.objects.get(id=selected_option_id)
                        is_correct = selected_option.is_correct
                        
                        Answer.objects.create(
                            question=question,
                            attempt=attempt,
                            selected_option=selected_option,
                            is_correct=is_correct
                        )
                        
                        if is_correct:
                            correct_count += 1
            
            # Calculate percentage
            if total_questions > 0:
                attempt.percentage_score = (correct_count / total_questions) * 100
                attempt.is_passed = attempt.percentage_score >= attempt.quiz.passing_score
            
            attempt.completed_at = timezone.now()
            attempt.answers_count = total_questions
            attempt.correct_answers = correct_count
            
            # Calculate and award points (only for 1st attempt)
            if attempt.attempt_number == 1:
                is_ai_quiz = attempt.quiz.created_by is None
                
                if is_ai_quiz:
                    # AI Quiz: 1 point per correct answer
                    points_earned = Decimal(str(correct_count * 1.0))
                else:
                    # Custom Quiz: 0.75-1 point per correct answer (average 0.875)
                    points_earned = Decimal(str(correct_count * 0.875))
                
                attempt.points_earned = points_earned
                
                # Add points to user's total (round to nearest integer)
                user.total_points += round(float(points_earned))
                user.save(update_fields=['total_points'])
                
                # Update user rankings
                update_user_rankings()
                
                print(f"🎯 Points awarded: {round(float(points_earned))} points to {user.name} (Quiz: {attempt.quiz.title}, AI: {is_ai_quiz}, Correct: {correct_count})")
            else:
                # No points for subsequent attempts
                attempt.points_earned = Decimal('0')
            
            attempt.save()
            
            # Show points earned message for first attempt
            if attempt.attempt_number == 1:
                messages.success(request, f'Quiz submitted! You scored {attempt.percentage_score:.1f}% and earned {int(attempt.points_earned)} points!')
            else:
                messages.success(request, f'Quiz submitted! You scored {attempt.percentage_score:.1f}%')
            
            return redirect('quiz_result', attempt_id=attempt.id)
    
    return redirect('quiz_detail', quiz_id=attempt.quiz.id)


@require_login
def quiz_result(request, attempt_id):
    """View quiz results"""
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=user)
    
    answers = attempt.answers.select_related('question', 'selected_option').all()
    
    # Group answers by question (important for checkbox questions with multiple answers)
    from collections import defaultdict
    question_answers = defaultdict(list)
    for answer in answers:
        question_answers[answer.question.id].append(answer)
    
    # Build results with all answers per question
    results = []
    processed_questions = set()
    
    for answer in answers:
        question = answer.question
        if question.id in processed_questions:
            continue
        processed_questions.add(question.id)
        
        options = list(question.options.all())
        answers_for_question = question_answers[question.id]
        selected_options = [ans.selected_option for ans in answers_for_question]
        
        # For checkbox questions, all Answer records have same is_correct value
        is_correct = answers_for_question[0].is_correct if answers_for_question else False
        
        results.append({
            'question': question,
            'options': options,
            'selected_options': selected_options,  # Now a list
            'selected_option': selected_options[0] if selected_options else None,  # For backward compatibility
            'is_correct': is_correct
        })
    
    # Check if it's an AI quiz
    is_ai_quiz = attempt.quiz.created_by is None
    
    return render(request, 'quiz/quiz_result.html', {
        'attempt': attempt,
        'results': results,
        'is_ai_quiz': is_ai_quiz,
        'selected_study_plan': attempt.quiz.study_plan,
        'name': request.session.get("app_user_name", "User")
    })


@require_login
def quiz_stats(request):
    """Display quiz statistics for user's study plans"""
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    
    # Check if filtering by study plan
    study_plan_id = request.GET.get('study_plan')
    selected_study_plan = None
    
    if study_plan_id:
        try:
            selected_study_plan = StudyPlan.objects.get(id=study_plan_id, user=user)
            # Get quizzes for this specific study plan
            quizzes = Quiz.objects.filter(study_plan=selected_study_plan)
        except StudyPlan.DoesNotExist:
            quizzes = Quiz.objects.filter(study_plan__user=user)
    else:
        # Get all quizzes from user's study plans
        quizzes = Quiz.objects.filter(study_plan__user=user)
    
    # Get all user's attempts for these quizzes
    attempts = QuizAttempt.objects.filter(
        user=user,
        quiz__in=quizzes
    ).select_related('quiz').order_by('-started_at')
    
    # Calculate statistics
    total_attempts = attempts.count()
    completed_attempts = attempts.filter(completed_at__isnull=False).count()
    passed_attempts = sum(1 for attempt in attempts if attempt.is_passed)
    
    # Get quiz-specific stats
    quiz_stats = []
    for quiz in quizzes:
        quiz_attempts = QuizAttempt.objects.filter(user=user, quiz=quiz)
        best_attempt = quiz_attempts.order_by('-total_score').first()
        
        quiz_stats.append({
            'quiz': quiz,
            'attempts_count': quiz_attempts.count(),
            'best_score': best_attempt.percentage_score if best_attempt else 0,
            'best_attempt': best_attempt
        })
    
    return render(request, 'quiz/quiz_stats.html', {
        'selected_study_plan': selected_study_plan,
        'quizzes': quizzes,
        'attempts': attempts,
        'quiz_stats': quiz_stats,
        'total_attempts': total_attempts,
        'completed_attempts': completed_attempts,
        'passed_attempts': passed_attempts,
        'name': request.session.get("app_user_name", "User")
    })


@require_login
def leaderboard(request):
    """Display global leaderboard based on total points"""
    user_id = request.session.get("app_user_id")
    current_user = User.objects.get(id=user_id)
    
    # Get top 100 users ordered by points
    top_users = User.objects.all().order_by('-total_points', 'id')[:100]
    
    # Get current user's rank and nearby users
    user_rank = current_user.current_rank if current_user.current_rank > 0 else User.objects.filter(total_points__gt=current_user.total_points).count() + 1
    
    return render(request, 'quiz/leaderboard.html', {
        'top_users': top_users,
        'current_user': current_user,
        'user_rank': user_rank,
        'name': request.session.get("app_user_name", "User")
    })
