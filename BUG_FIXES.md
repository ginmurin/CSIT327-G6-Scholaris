# Bug Fixes and Solutions

## 🐛 Issue #1: Progress Bar Doesn't Connect to AI Resources
**Problem**: Progress bar shows 0% and doesn't update when marking resources complete.

**Root Cause**: The `ResourceProgress` model is linked to `StudyPlanResource`, but AI resources are being displayed directly without proper `StudyPlanResource` linkage.

**Solution**:
```python
# In studyplan/views.py - get_resources() function
# CURRENT ISSUE: Resources are added to display but resource ID doesn't match StudyPlanResource ID

# FIX: Change line ~270 where resources.append() is called
resources.append({
    "id": spr.id,  # ❌ This is StudyPlanResource ID, not Resource ID
    # Should use resource.id for the resource itself
    # But toggle needs StudyPlanResource ID
})

# BETTER APPROACH: 
resources.append({
    "id": resource.id,  # Resource ID for display
    "spr_id": spr.id,   # StudyPlanResource ID for toggle
    "title": resource.title,
    # ... rest of fields
    "is_completed": spr.is_completed,
})

# Then update resources.html to use spr_id for toggle:
onclick="toggleCompletion({{ study_plan.id }}, {{ resource.spr_id }}, this)"
```

**Quick Fix Steps**:
1. Modify `get_resources()` view to return both `resource.id` and `spr.id`
2. Update `resources.html` template to use correct ID for toggle
3. Ensure `toggle_resource_completion()` uses `StudyPlanResource` ID

---

## 🐛 Issue #2: Study Plan Can't Be Deleted
**Problem**: Delete button doesn't work or throws error.

**Root Cause**: Foreign key constraints from `Progress` and `ResourceProgress` models preventing deletion.

**Solution**:
```python
# Check studyplan/models.py for CASCADE settings
class StudyPlan(models.Model):
    # Ensure related models have on_delete=CASCADE

# In progress/models.py
class Progress(models.Model):
    study_plan = models.ForeignKey(StudyPlan, on_delete=models.CASCADE)  # ✅ Should CASCADE

class ResourceProgress(models.Model):
    study_plan_resource = models.ForeignKey(StudyPlanResource, on_delete=models.CASCADE)  # ✅ Should CASCADE
```

**Fix**: Update `delete_study_plan()` view to manually delete related records:
```python
@require_login
def delete_study_plan(request, plan_id):
    user_id = request.session.get("app_user_id")
    user = User.objects.get(id=user_id)
    study_plan = get_object_or_404(StudyPlan, id=plan_id, user=user)
    
    if request.method == 'POST':
        from progress.models import Progress, ResourceProgress
        
        title = study_plan.title
        
        try:
            # Manually delete related records first
            Progress.objects.filter(study_plan=study_plan).delete()
            
            # Delete StudyPlanResources (which will cascade to ResourceProgress)
            study_plan.plan_resources.all().delete()
            
            # Now delete the study plan
            study_plan.delete()
            
            messages.success(request, f'Study plan "{title}" deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting study plan: {str(e)}')
            print(f"Error during deletion: {e}")
        
        return redirect('list_study_plans')
    
    return render(request, 'studyplan/delete_confirm.html', {
        'study_plan': study_plan,
        'name': request.session.get("app_user_name", "User")
    })
```

---

## 🐛 Issue #3: AI Doesn't Provide Resources
**Problem**: Resources page shows "No resources found" or 0 resources.

**Root Cause**: 
1. Gemini API rate limiting (429 errors)
2. API key might be invalid
3. Response parsing errors

**Solutions**:

### A. Check API Key
```bash
# Test your API key
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GEMINI_API_KEY'))"
```

### B. Add Better Error Logging
```python
# In core/ai_service.py - suggest_resources() method
@staticmethod
def suggest_resources(topic, learning_objective=None, resource_types=None, limit=10):
    try:
        # ... existing code ...
        
        response = LearningAIService._call_ai_with_retry(
            model_name="gemini-2.0-flash-exp",
            prompt=prompt
        )
        
        # Add logging
        print(f"🤖 AI Response received: {response[:200]}...")  # First 200 chars
        
        # ... parse response ...
        
        resources = json.loads(result_text.strip())
        print(f"✅ Parsed {len(resources)} resources successfully")
        
        return resources
        
    except Exception as e:
        print(f"❌ ERROR in suggest_resources: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return empty list instead of raising
        return []
```

### C. Test Manually
```python
# Create test script: test_ai.py
from core.ai_service import LearningAIService

resources = LearningAIService.suggest_resources(
    topic="Python Programming",
    learning_objective="Learn basics",
    limit=5
)

print(f"Got {len(resources)} resources:")
for r in resources:
    print(f"- {r.get('title')}")
```

---

## 🐛 Issue #4: Start Date Can Be Set in the Past
**Problem**: User can create study plan with start date before today.

**Root Cause**: Form validation only sets `min` attribute in HTML, but doesn't validate server-side.

**Solution**:
```python
# In studyplan/forms.py
from django import forms
from .models import StudyPlan
from datetime import date

class StudyPlanForm(forms.ModelForm):
    class Meta:
        model = StudyPlan
        fields = ['title', 'description', 'learning_objective', 'start_date', 'end_date', 
                  'preferred_resources', 'estimated_hours_per_week']
        # ... existing widgets ...
    
    def clean_start_date(self):
        """Validate start date is not in the past"""
        start_date = self.cleaned_data.get('start_date')
        
        if start_date and start_date < date.today():
            raise forms.ValidationError("Start date cannot be in the past.")
        
        return start_date
    
    def clean_end_date(self):
        """Validate end date is after start date"""
        end_date = self.cleaned_data.get('end_date')
        start_date = self.cleaned_data.get('start_date')
        
        if end_date and start_date and end_date < start_date:
            raise forms.ValidationError("End date must be after start date.")
        
        if end_date and end_date < date.today():
            raise forms.ValidationError("End date cannot be in the past.")
        
        return end_date
```

---

## 🐛 Issue #5: Password & Email Changes Don't Update Database
**Problem**: Changing password or email doesn't persist to database.

**Root Cause**: Check if `save()` is actually being called with correct field updates.

**Debugging Steps**:
```python
# Add print statements to verify
def change_password_view(request):
    user_id = request.session.get("app_user_id")
    user = get_object_or_404(AppUser, id=user_id)
    
    if request.method == "POST":
        form = ChangePasswordForm(request.POST, user=user)
        if form.is_valid():
            new_password = form.cleaned_data['new_password1']
            
            print(f"🔐 Old password hash: {user.password[:20]}...")
            
            user.password = make_password(new_password)
            
            print(f"🔐 New password hash: {user.password[:20]}...")
            
            user.save(update_fields=['password'])
            
            print(f"✅ Password saved to database")
            
            # Verify it saved
            user.refresh_from_db()
            print(f"🔍 Verified password hash: {user.password[:20]}...")
            
            messages.success(request, "Password changed successfully!")
            return redirect("profile")
    # ... rest of code
```

**Potential Fix**: Remove `update_fields` to save all fields:
```python
# Instead of:
user.save(update_fields=['password'])

# Try:
user.save()  # Save all fields
```

**OR** Verify the field name matches the model:
```python
# Check authentication/models.py
class User(models.Model):
    password = models.CharField(max_length=255)  # ✅ Field name should match
```

---

## 📋 Testing Checklist

After applying fixes, test:

- [ ] Create new study plan with today's date ✅
- [ ] Try to set start date to yesterday (should fail) ❌
- [ ] AI generates resources (check terminal for logs)
- [ ] Mark resource as complete (toggle shows DONE)
- [ ] Progress bar updates to 50% (if 1 of 2 resources)
- [ ] Delete study plan (should work without errors)
- [ ] Change password (logout and login with new password)
- [ ] Change email (check profile shows new email)

---

## 🚀 Priority Fix Order

1. **HIGH**: Fix date validation (security/UX issue)
2. **HIGH**: Fix password/email updates (critical functionality)
3. **MEDIUM**: Fix AI resource generation (core feature)
4. **MEDIUM**: Fix progress bar connection (UX issue)
5. **LOW**: Fix study plan deletion (workaround: manual DB cleanup)

---

## 💡 Quick Commands for Testing

```bash
# Check database for study plan
python manage.py shell
>>> from studyplan.models import StudyPlan
>>> StudyPlan.objects.all()

# Check if password updated
>>> from authentication.models import User
>>> u = User.objects.get(id=1)
>>> u.password  # Should be hashed

# Test AI service
>>> from core.ai_service import LearningAIService
>>> resources = LearningAIService.suggest_resources("Python", limit=3)
>>> len(resources)

# Check Progress
>>> from progress.models import Progress
>>> Progress.objects.all().values()
```
