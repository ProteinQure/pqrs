import collections

import npyscreen

from pqrs.config import config


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
        """
        Switch the description widget content to the currently focused form
        element's description.
        """

        if not getattr(self.parent_form, 'description', None):
            return None
        self.parent_form.description.values = self.description_text
        self.parent_form.display()

    def on_focusout(self):
        """
        Clear the description widget content on focus out.
        """

        if not getattr(self.parent_form, 'description', None):
            return None
        self.parent_form.description.values = []


class RoleSelectorForm(npyscreen.Form):
    """
    Form displaying the available roles and their description.
    """

    def __init__(self, *args, **kwargs):
        self.data = kwargs.pop('data')
        self.checkboxes = collections.defaultdict(list)
        super().__init__(*args, **kwargs)

    def afterEditing(self):
        """
        Sets the next form to displayed.
        """

        self.parentApp.addForm('config', ReviewConfigurationForm, name='Provide configuration', data=self.data)
        self.parentApp.setNextForm('config')

    def create(self):
        """
        Constructs the form, displaying a checkbox for each role and a
        description widget.
        """

        for collection, roles in self.data.items():
            # Create channel header
            self.add(
                npyscreen.TitleFixedText,
                name=f"Channel: {collection}",
                value="",
                max_width=40,
                editable=False
            )

            # Create a checkbox for each role in the channel
            for role in roles:
                checkbox = self.add(
                    DescribedCheckBox,
                    name=role.name,
                    value=role.selected,
                    max_width=40,
                    parent_form=self,
                    description_text=role.description
                )
                self.checkboxes[collection].append(checkbox)

            self.nextrely += 1  # padding

        self.description = self.add(
            npyscreen.BoxTitle,
            name="Description",
            relx=50,
            rely=1,
            editable=False,
            max_height=20
        )


class ReviewConfigurationForm(npyscreen.Form):
    """
    Form displaying the available roles and their description.
    """

    def __init__(self, *args, **kwargs):
        self.data = kwargs.pop('data')
        self.elements = {}
        super().__init__(*args, **kwargs)

    def afterEditing(self):
        """
        Sets the next form to displayed.
        """

        # This is the final form
        self.parentApp.setNextForm(None)

    def add_form_item(self, name, value, item_type):
        """
        Add a single element to the form.
        """

        # Do nothing of widget with this name already exists
        if name in self.elements:
            return

        element_value = config.get_variable(name) or value

        element = self.add(npyscreen.TitleText, name=name, value=element_value, use_two_lines=False)
        self.elements[name] = element

    def create(self):
        """
        Construct the form by displaying TitleText input for each configuration
        variable the selected roles require.
        """

        for collection, roles in self.data.items():
            for index, role in enumerate(roles):
                # Determine if the checkbox was selected, continue if not
                if not self.parentApp._Forms["MAIN"].checkboxes[collection][index].value:
                    continue

                variables = role.variables
                for variable, default in variables.items():
                    if isinstance(default, dict):
                        for subvariable, subdefault in default.items():
                            self.add_form_item(f"{variable}.{subvariable}", subdefault, 'textfield')
                    else:
                        self.add_form_item(variable, default, 'textfield')

    @property
    def values(self):
        # type: () -> dict[str, bool]
        """
        Return the values from the user-filled form.
        """

        return {k: v.value for k, v in self.elements.items()}


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
    # type: (dict[str, list[Role]) -> tuple[list[Role], dict[str, str]]
    """
    Returns user-selected roles.
    """

    app = RoleSelector(data)
    app.run()

    variables = app._Forms["config"].values

    selected_roles = {
        collection: [
            role for role, checkbox in zip(roles, app._Forms["MAIN"].checkboxes[collection])
            if checkbox.value is True
        ]
        for collection, roles in data.items()
    }

    return selected_roles, variables
