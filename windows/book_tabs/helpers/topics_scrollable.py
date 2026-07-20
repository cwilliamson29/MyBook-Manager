import customtkinter as ctk


class TopicsFrame(ctk.CTkScrollableFrame):

    def __init__(self, parent, topics):
        super().__init__(parent, width=220, height=50, fg_color="transparent")

        self.topics_vars = {}

        for topics_id, topics_name in topics:

            var = ctk.BooleanVar(value=False)

            checkbox = ctk.CTkCheckBox(
                self,
                text=topics_name,
                variable=var
            )

            checkbox.pack(
                anchor="w",
                padx=10,
                pady=2
            )

            self.topics_vars[topics_id] = var

    def get_selected_topics(self):
        """Returns a list of selected category IDs."""

        return [
            topics_id
            for topics_id, var in self.topics_vars.items()
            if var.get()
        ]

    def set_selected_topics(self, selected_ids):
        """Checks the boxes whose IDs are in selected_ids."""

        for topics_id, var in self.topics_vars.items():
            var.set(topics_id in selected_ids)

    def clear(self):
        """Uncheck all categories."""

        for var in self.topics_vars.values():
            var.set(False)