from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from django.http import JsonResponse
from .models import Lead, LeadNote
from .forms import LeadForm, LeadNoteForm

@login_required
def lead_list(request):
    leads = Lead.objects.select_related('atendente').all().order_by('-created_at')
    form = LeadForm()
    return render(request, 'crm/lead_list.html', {'leads': leads, 'form': form})

@login_required
@require_http_methods(["POST"])
def lead_create_ajax(request):
    form = LeadForm(request.POST)
    if form.is_valid():
        lead = form.save(commit=False)
        lead.atendente = request.user
        lead.save()
        row_html = render_to_string('crm/partials/lead_table_row.html', {'lead': lead}, request=request)
        return JsonResponse({'success': True, 'row_html': row_html})
    else:
        form_html = render_to_string('crm/partials/lead_form_partial.html', {'form': form}, request=request)
        return JsonResponse({'success': False, 'form_html': form_html})

@login_required
def lead_detail(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)
    notes = lead.notes.all().order_by('-created_at')

    if request.method == 'POST':
        note_form = LeadNoteForm(request.POST)
        if note_form.is_valid():
            note = note_form.save(commit=False)
            note.lead = lead
            note.user = request.user
            note.save()
            return redirect('lead_detail', lead_id=lead.id)
    else:
        note_form = LeadNoteForm()

    return render(request, 'crm/lead_detail.html', {
        'lead': lead,
        'notes': notes,
        'note_form': note_form
    })

@login_required
@require_http_methods(["GET", "POST"])
def lead_edit_ajax(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)

    if request.method == 'POST':
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            row_html = render_to_string('crm/partials/lead_table_row.html', {'lead': lead}, request=request)
            return JsonResponse({'success': True, 'row_html': row_html})
        else:
            form_html = render_to_string('crm/partials/lead_edit_form.html', {'form': form}, request=request)
            return JsonResponse({'success': False, 'form_html': form_html})
    else:
        form = LeadForm(instance=lead)
        form_html = render_to_string('crm/partials/lead_edit_form.html', {'form': form}, request=request)
        return JsonResponse({'form_html': form_html})

@login_required
@require_http_methods(["POST"])
def lead_delete_ajax(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)
    lead.delete()
    return JsonResponse({'success': True})
