from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
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


@require_login
def quiz_list(request):
    """Display all quizzes for the logged-in user"""
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
            # Available quizzes (reserved for AI-generated quizzes in the future)
            study_plan_quizzes = Quiz.objects.filter(study_plan=selected_study_plan).exclude(created_by=user)
        except StudyPlan.DoesNotExist:
            my_quizzes = Quiz.objects.filter(created_by=user)
            study_plan_quizzes = Quiz.objects.filter(study_plan__user=user).exclude(created_by=user)
    else:
        # Get all quizzes created by user
        my_quizzes = Quiz.objects.filter(created_by=user)
        # Available quizzes (reserved for AI-generated quizzes in the future)
        study_plan_quizzes = Quiz.objects.filter(study_plan__user=user).exclude(created_by=user)
    
    return render(request, 'quiz/quiz_list.html', {
        'my_quizzes': my_quizzes,
        'study_plan_quizzes': study_plan_quizzes,
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
            quiz.save()
            messages.success(request, f'Quiz "{quiz.title}" created! Now add questions.')
            return redirect('add_question', quiz_id=quiz.id)
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
                    return redirect('add_question', quiz_id=quiz.id)
                else:
                    return redirect('quiz_detail', quiz_id=quiz.id)
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
def quiz_detail(request, quiz_id):
    """View quiz details and questions"""
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check if user can access this quiz
    can_edit = quiz.created_by == user
    
    questions = quiz.questions.prefetch_related('options').all()
    
    # Get user's attempts
    attempts = QuizAttempt.objects.filter(quiz=quiz, user=user).order_by('-started_at')
    
    return render(request, 'quiz/quiz_detail.html', {
        'quiz': quiz,
        'questions': questions,
        'can_edit': can_edit,
        'attempts': attempts,
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
                return redirect('quiz_detail', quiz_id=question.quiz.id)
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
        return redirect('quiz_detail', quiz_id=quiz.id)
    
    return render(request, 'quiz/delete_question.html', {
        'question': question,
        'name': request.session.get("app_user_name", "User")
    })


@require_login
def publish_quiz(request, quiz_id):
    """Publish a quiz"""
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    quiz = get_object_or_404(Quiz, id=quiz_id, created_by=user)
    
    if quiz.questions.count() == 0:
        messages.error(request, 'Cannot publish a quiz without questions!')
        return redirect('quiz_detail', quiz_id=quiz.id)
    
    quiz.status = 'published'
    quiz.save()
    messages.success(request, f'Quiz "{quiz.title}" has been published!')
    return redirect('quiz_detail', quiz_id=quiz.id)


@require_login
def take_quiz(request, quiz_id):
    """Take a quiz"""
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check if quiz is published
    if quiz.status != 'published':
        messages.error(request, 'This quiz is not published yet!')
        return redirect('quiz_list')
    
    # Check attempts
    attempts_count = QuizAttempt.objects.filter(quiz=quiz, user=user).count()
    if quiz.max_attempts and attempts_count >= quiz.max_attempts:
        messages.error(request, 'You have reached the maximum number of attempts for this quiz!')
        return redirect('quiz_detail', quiz_id=quiz.id)
    
    # Create new attempt
    attempt = QuizAttempt.objects.create(
        quiz=quiz,
        user=user,
        study_plan=quiz.study_plan,
        attempt_number=attempts_count + 1
    )
    
    questions = quiz.questions.prefetch_related('options').all()
    
    if quiz.shuffle_questions:
        questions = list(questions)
        import random
        random.shuffle(questions)
    
    return render(request, 'quiz/take_quiz.html', {
        'quiz': quiz,
        'attempt': attempt,
        'questions': questions,
        'name': request.session.get("app_user_name", "User")
    })


@require_login
def submit_quiz(request, attempt_id):
    """Submit quiz answers"""
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=user)
    
    if request.method == 'POST':
        with transaction.atomic():
            correct_count = 0
            total_points = 0
            earned_points = 0
            
            for question in attempt.quiz.questions.all():
                total_points += question.points
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
                        earned_points += question.points
            
            # Update attempt
            attempt.completed_at = timezone.now()
            attempt.total_score = earned_points
            attempt.answers_count = attempt.quiz.total_questions
            attempt.correct_answers = correct_count
            
            if total_points > 0:
                attempt.percentage_score = (earned_points / total_points) * 100
                attempt.is_passed = attempt.percentage_score >= attempt.quiz.passing_score
            
            attempt.save()
            
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
    
    # Group answers with questions and options
    results = []
    for answer in answers:
        question = answer.question
        options = list(question.options.all())
        results.append({
            'question': question,
            'options': options,
            'selected_option': answer.selected_option,
            'is_correct': answer.is_correct
        })
    
    return render(request, 'quiz/quiz_result.html', {
        'attempt': attempt,
        'results': results,
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
