# -*- coding: utf-8 *-*
from selene import options
from wtforms import (Form, TextField, BooleanField, TextAreaField, RadioField,
                     SelectField)
from wtforms.validators import Required, Email


class NewPostForm(Form):

    title = TextField(validators=[Required()])
    slug = BooleanField()
    customslug = TextField()
    tags = TextField(validators=[Required()])
    content = TextAreaField(validators=[Required()])
    status = RadioField(validators=[Required()], choices=options.STATUSES)
    text_type = SelectField(validators=[Required()],
        choices=options.get_allowed_text_types())


class NewCommentForm(Form):

    name = TextField(validators=[Required()])
    email = TextField(validators=[Required(), Email()])
    content = TextAreaField(validators=[Required()])


class SearchForm(Form):

    q = TextField(validators=[Required()])
