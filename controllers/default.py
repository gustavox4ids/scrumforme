# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################


def index():
    all_projects = db(Project).select()

    response.flash = T("Welcome to scrumforme!")
    return dict(all_projects=all_projects)


def projects():
    from datetime import datetime

    all_projects = db(Project).select()

    form = SQLFORM.factory(
        Field('name', label=T('Name'), requires=IS_NOT_EMPTY(error_message=T('The field name can not be empty!'))),
        Field('description', label= T('Description')),
        Field('url', label= 'Url'),
        table_name='projects',
        submit_button=T('CREATE')
        )

    if form.accepts(request.vars):
        project_id = Project.insert(
                        name=form.vars.name,
                        description=form.vars.description,
                        url=form.vars.url,
                        date_=datetime.now(),
                        )
        redirect(URL(f="product_backlog",args=[project_id]))
    elif form.errors:
        response.flash = T('Formulário contem erros. Por favor, verifique!')

    return dict(form=form, all_projects=all_projects)


def product_backlog():
    all_projects = db(Project).select()
    project_id = request.args(0) or redirect(URL('projects'))
    project = db(Project.id == project_id).select().first()

    stories = db(Story.project_id == project_id).select()
    sprint = db(Sprint.project_id == project_id).select().first()

    form_sprint = SQLFORM.factory(
        Field('name', label=T('Name'), requires=IS_NOT_EMPTY(error_message=T('The field name can not be empty!'))),
        Field('weeks', label=T('Weeks'), requires=IS_NOT_EMPTY(error_message=T('The field name can not be empty!'))),
        table_name='sprint',
        submit_button=T('CREATE')
        )

    if form_sprint.process().accepted:
        name = form_sprint.vars['name']
        weeks = form_sprint.vars['weeks']

        sprint_id = Sprint.insert(project_id=project_id,
            name=name, weeks=weeks)

        redirect(URL(f='product_backlog', args=[project_id]))

    definition_ready = {}
    for story in stories:
        definition_ready[story.id] = db(Definition_ready.story_id == story.id).select()

    tasks = {}
    for row in definition_ready:
        for df in definition_ready[row]:
            tasks[df.id] = db(Task.definition_ready_id == df.id).select()

    if stories:
        return dict(project=project, all_projects=all_projects, stories=stories, definition_ready=definition_ready, tasks=tasks, form_sprint=form_sprint, sprint=sprint)
    else:
        return dict(project=project, all_projects=all_projects, form_sprint=form_sprint, sprint=sprint)


def create_update_backlog_itens():
    """Function that creates or updates items. Receive updates if request.vars.dbUpdate and takes the ID to be updated with request.vars.dbID
    """

    if request.vars:
        if request.vars.dbUpdate == "true":
            if request.vars.name == "story":
                db(Story.id == request.vars.dbID).update(
                    title=request.vars.value,
                )
            elif request.vars.name == "definition_ready":
                db(Definition_ready.id == request.vars.dbID).update(
                    title=request.vars.value,
                )
            elif request.vars.name == "task":
                db(Task.id == request.vars.dbID).update(
                    title=request.vars.value,
                )

            return dict(success="success",msg="gravado com sucesso!")

        elif request.vars.dbUpdate == "false":
            if request.vars.name == "story":
                database_id = Story.insert(
                        project_id=request.vars.pk,
                        title=request.vars.value
                        )
            elif request.vars.name == "definition_ready":
                database_id = Definition_ready.insert(
                            story_id=request.vars.pk,
                            title=request.vars.value
                            )
            elif request.vars.name == "task":
                database_id = Task.insert(
                            definition_ready_id=request.vars.pk,
                            title=request.vars.value
                            )

            return dict(success="success",msg="gravado com sucesso!",database_id=database_id)

    else:
        return dict(error="error",msg="erro ao gravar!")


def remove_item_backlog_itens():

    if request.vars:
        if request.vars.name == "task":
            db(Task.id == request.vars.pk).delete()

        if request.vars.name == "definition_ready":
            db(Definition_ready.id == request.vars.pk).delete()
            definitions_ready_data = db(Definition_ready.id == request.vars.pk).select()
            
            for df in definitions_ready_data:
                db(Task.definition_ready_id == df.id).delete()
        
        elif request.vars.name == "story":
            db(Story.id == request.vars.pk).delete()
            definitions_ready_data = db(Definition_ready.story_id == request.vars.pk).select()
            
            for df in definitions_ready_data:
                db(Definition_ready.id == df.id).delete()
                db(Task.definition_ready_id == df.id).delete()

        return True
    else:
        return False


def change_ajax_itens():

    if request.vars:
        print request.vars
        if request.vars.story_points:
            db(Story.id == request.vars.story_id).update(
                story_points=request.vars.story_points,
            )
        elif request.vars.benefit:
            db(Story.id == request.vars.story_id).update(
                benefit=request.vars.benefit,
            )
        elif request.vars.sprint_id:
            if request.vars.name == "sprint":
                db(Story.id == request.vars.story_id).update(
                    sprint_id=request.vars.sprint_id,
                )
            elif request.vars.name == "backlog":
                db(Story.id == request.vars.story_id).update(
                sprint_id=None,
            )

        return True
    else:
        return False


def launch_sprint():
    from datetime import datetime
    sprint_id = request.args(0) or redirect(URL('index'))
    sprint = db(Sprint.id==sprint_id).select().first()
    if not sprint.started:
        db(Sprint.id==sprint_id).update(started=datetime.today().date())
    redirect(URL(f='projects'))


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())
