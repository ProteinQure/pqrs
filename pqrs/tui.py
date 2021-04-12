import npyscreen


class DescribedCheckBox(npyscreen.CheckBox):
    """
    Checkbox that displays a description of the given checkbox in the parent form.
    Note: This expects that the parent form has a widget attribute called 'description'.
    """

    def __init__(self, *args, **kwargs):
        self.parent_form = kwargs.pop('parent_form')
        self.description_text = kwargs.pop('description_text')
        super().__init__(*args, **kwargs)

    def on_focusin(self):
        if not getattr(self.parent_form, 'description', None):
            return None
        self.parent_form.description.values = self.description_text
        self.parent_form.display()

    def on_focusout(self):
        if not getattr(self.parent_form, 'description', None):
            return None
        self.parent_form.description.values = []


class RoleSelectorForm(npyscreen.Form):
    """
    Form displaying the available roles and their description.
    """

    def __init__(self, *args, **kwargs):
        self.data = kwargs.pop('data')
        self.checkboxes = []
        super().__init__(*args, **kwargs)

    def afterEditing(self):
        self.parentApp.setNextForm(None)

    def create(self):
        for role in self.data:
            checkbox = self.add(
                DescribedCheckBox,
                name=role.name,
                value=role.selected,
                max_width=40,
                parent_form=self,
                description_text=role.description
            )
            self.checkboxes.append(checkbox)

        self.description = self.add(
            npyscreen.BoxTitle,
            name="Description",
            relx=50,
            rely=1,
            editable=False,
            max_height=20
        )


class RoleSelector(npyscreen.NPSAppManaged):
    """
    Ncurses-based application to select appropriate roles to install on the
    workstation.
    """

    def __init__(self, data):
        self.data = data
        super().__init__()

    def onStart(self):
        npyscreen.setTheme(npyscreen.Themes.ColorfulTheme)
        self.addForm('MAIN', RoleSelectorForm, name='Select roles', data=self.data)


def select_roles(data):
    """
    Returns user-selected roles.
    """
    app = RoleSelector(data)
    app.run()

    return [
        role for role, checkbox in zip(data, app._Forms["MAIN"].checkboxes)
        if checkbox.value is True
    ]
