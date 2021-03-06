from flask import (Blueprint,
                   render_template,
                   redirect,
                   url_for,
                   request)

from flask_login import login_required, current_user

from nokkhum import models

from .. import forms
# import asyncio
import datetime


module = Blueprint('projects', __name__, url_prefix='/projects')


@module.route('/')
@login_required
def index():
    my_projects = list()
    projects = models.Project.objects().order_by('-id')
    for project in projects:
        if (project.is_member(current_user._get_current_object()) is True) or (project.owner == current_user._get_current_object()) or ('admin' in current_user.roles):
            my_projects.append(project)
        # Q(owner=current_user._get_current_object())).order_by('-id')
    return render_template('/projects/index.html',
                           projects=my_projects,
                           now=datetime.datetime.now())


@module.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = forms.projects.ProjectForm()
    if not form.validate_on_submit():
        # print('>>>>>>>>>>>',form.has_token.data)
        return render_template('/projects/create-project.html',
                               form=form)
    project = models.Project()
    form.populate_obj(project)
    project.owner = current_user._get_current_object()
    project.users.append(current_user._get_current_object())
    now = datetime.datetime.now()
    if project.created_date is None:
        project.created_date = now
    project.updated_date = now
    project.save()
    return redirect(url_for('projects.index'))


@module.route('/<project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(project_id):
    project = models.Project.objects.get(id=project_id)
    form = forms.projects.ProjectForm(obj=project)
    if not form.validate_on_submit():
        return render_template('/projects/edit-project.html',
                               form=form,
                               project=project)
    form.populate_obj(project)
    project.save()
    return redirect(url_for('projects.index'))


@module.route('/<project_id>/view', methods=['GET'])
@login_required
def view(project_id):
    project = None
    if 'admin' in current_user.roles:
        project = models.Project.objects.get(
                id=project_id)
    else:
        project = models.Project.objects.get(
                id=project_id)
        if (project.is_member(current_user._get_current_object()) is False):
            project = None

    if project is None:
        return redirect('dashboard.index')

    processors = models.Processor.objects(project=project)
    return render_template('/projects/project.html',
                           project=project,
                           processors=processors)


@module.route('/<project_id>/delete', methods=['GET', 'POST'])
@login_required
def delete(project_id):
    project = None
    if 'admin' in current_user.roles:
        project = models.Project.objects.get(
                id=project_id)
    else:
        project = models.Project.objects.get(
                id=project_id,
                owner=current_user._get_current_object())
    if project is None:
        return redirect('dashboard.index')
    for camera in project.cameras:
        camera.status = 'Inactive'
        camera.save()
    project.status = 'Inactive'
    project.save()
    return redirect(url_for('projects.index'))


@module.route('/<project_id>/add_contributor_page')
@login_required
def add_contributor_page(project_id):
    users = models.User.objects()
    project = models.Project.objects.get(id=project_id)
    return render_template('/projects/add-contributor.html',
                           project=project,
                           users=users)


@module.route('/<project_id>/add_contributor', methods=['GET'])
@login_required
def add_contributor(project_id):
    users = models.User.objects()
    project = models.Project.objects.get(id=project_id)
    added_user_id = request.args.get('add-user')
    if added_user_id:
        added_user = models.User.objects.get(id=added_user_id)
        if added_user not in project.users:
            project.users.append(added_user)
            project.save()
    return render_template('/projects/add-contributor.html',
                           project=project,
                           users=users)

@module.route('/<project_id>/delete_contributor/<user_id>', methods=['GET'])
@login_required
def delete_contributor(project_id, user_id):
    users = models.User.objects()
    project = None
    if 'admin' in current_user.roles:
        project = models.Project.objects.get(
                id=project_id)
    else:
        project = models.Project.objects.get(
                id=project_id,
                owner=current_user._get_current_object())
    delete_user = models.User.objects.get(id=user_id)
    if delete_user in project.users:
        project.users.remove(delete_user)
    if delete_user in project.assistant:
        project.assistant.remove(delete_user)
    project.save()
    return render_template('/projects/add-contributor.html',
                           project=project,
                           users=users)

@module.route('/<project_id>/add_assistant/<user_id>', methods=['GET'])
@login_required
def add_assistant(project_id, user_id):
    users = models.User.objects()
    project = models.Project.objects.get(id=project_id)
    assistant = models.User.objects.get(id=user_id)
    if assistant not in project.assistant:
        project.assistant.append(assistant)
        project.save()
    return render_template('/projects/add-contributor.html',
                           project=project,
                           users=users)
