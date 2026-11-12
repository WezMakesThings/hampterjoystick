#--------------------------------------------------------------
#  Copyright (C) 2025 EscapedShadows
#
#  Distributed under the terms of the Apache 2.0 License.
#--------------------------------------------------------------

import darkdetect
import customtkinter as ctk
import pygame
import platform
import subprocess

if platform.system().lower() == "linux":
    def theme():
        try:
            # Capture color-scheme
            cs_out = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                capture_output=True, text=True
            )
            cs_stdout = cs_out.stdout.lower().strip()

            # Capture gtk-theme
            gt_out = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
                capture_output=True, text=True
            )
            gt_stdout = gt_out.stdout.lower().strip()

        except Exception:
            return "Light"

        if "-dark" in gt_stdout or "-dark" in cs_stdout:
            return "Dark"
        return "Light"
    
    darkdetect.theme = theme

# Init pygame
pygame.init()
pygame.joystick.init()

ctk.set_appearance_mode(darkdetect.theme().lower())

app = ctk.CTk()
app.geometry("400x600")
app.title("Joystick Visualizer")

# Globals
joystick_refs = []
axis_labels = []
button_labels = []
current_selection = None


# Joystick update functions
def update_joysticks(js_element: ctk.CTkComboBox):
    global joystick_refs
    selected_joystick = None
    joystick_refs = []
    values = []

    for i in range(pygame.joystick.get_count()):
        joystick = pygame.joystick.Joystick(i)
        joystick.init()
        joystick_refs.append(joystick)
        values.append(f"{i+1}: {joystick.get_name()}")

    # Apply joysticks to selection box
    js_element.configure(values=values)
    if joystick_refs:
        setup_joystick_display(
            joystick_refs[0]
        )  # Set the first available Joystick as selected, QoL changes planned later
        global current_selection
        current_selection = joystick_refs[0]
        js_element.set(values[0])


def setup_joystick_display(joystick):
    global axis_labels, button_labels

    # Clear previous
    for widget in axes_frame.winfo_children():
        widget.destroy()
    for widget in buttons_frame.winfo_children():
        widget.destroy()
    axis_labels.clear()
    button_labels.clear()

    # Dynamic detection planned
    def get_scaled_font(base_size=12):
        return ctk.CTkFont(size=base_size, weight="bold")

    # Axis bars
    for i in range(joystick.get_numaxes()):
        # Container frame for each axis
        axis_container = ctk.CTkFrame(axes_frame, height=40)
        axis_container.pack(fill="x", pady=3, padx=5)
        # axis_container.pack_propagate(False) # Maintain height

        # Bar background frame
        bar_frame = ctk.CTkFrame(
            axis_container, height=20, fg_color="gray20", corner_radius=10
        )
        bar_frame.pack(fill="x", pady=(5, 0))

        # Fill frame for positive/negative indication
        fill_frame = ctk.CTkFrame(
            bar_frame, height=20, fg_color="orange", corner_radius=10, width=0
        )
        fill_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Value label below the bar
        value_label = ctk.CTkLabel(
            axis_container, text=f"Axis {i+1}: 0.000", font=get_scaled_font()
        )
        value_label.pack(pady=(2, 0))

        axis_labels.append((bar_frame, fill_frame, value_label))

    # Button indicators
    for i in range(joystick.get_numbuttons()):
        button_frame = ctk.CTkFrame(buttons_frame, height=40)
        button_frame.pack(fill="x", pady=2, padx=5)
        # button_frame.pack_propagate(False)

        status_label = ctk.CTkLabel(
            button_frame,
            text=f"Button {i+1}: Released",
            font=get_scaled_font(),
            text_color="red",
        )
        status_label.pack(pady=5)

        button_labels.append(status_label)


def joystick_selected(choice):
    global current_selection
    if choice and joystick_refs:
        index_str, name = choice.split(": ", 1)
        index = int(index_str) - 1
        if 0 <= index < len(joystick_refs):
            current_selection = joystick_refs[index]
            setup_joystick_display(current_selection)


# Main layout
joystick_selector = ctk.CTkComboBox(app, values=[], command=joystick_selected, variable=ctk.StringVar(value="No Joystick found!"))
joystick_selector.grid(row=0, column=0, columnspan=2, pady=20, padx=20, sticky="ew")

axes_frame = ctk.CTkScrollableFrame(app, label_text="Controller Axes")
axes_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=10)

buttons_frame = ctk.CTkScrollableFrame(app, label_text="Controller Buttons")
buttons_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=10)

# Manual setup for Linux Machines (scrollwheel)
if platform.system().lower() == "linux":
    axes_frame.bind_all("<Button-4>", lambda e: axes_frame._parent_canvas.yview("scroll", -1, "units"))
    axes_frame.bind_all("<Button-5>", lambda e: axes_frame._parent_canvas.yview("scroll", 1, "units"))

    buttons_frame.bind_all("<Button-4>", lambda e: buttons_frame._parent_canvas.yview("scroll", -1, "units"))
    buttons_frame.bind_all("<Button-5>", lambda e: buttons_frame._parent_canvas.yview("scroll", 1, "units"))

# Configure grid weights for proper sizing
app.grid_rowconfigure(1, weight=1)
app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=1)

# Initialize joysticks
update_joysticks(joystick_selector)


# Joystick update loop
def update_joystick_values():
    global current_selection
    if current_selection is not None:
        pygame.event.pump()

        # Update axis values
        for i, (bar_frame, fill_frame, value_label) in enumerate(axis_labels):
            value = current_selection.get_axis(i)
            value_label.configure(text=f"Axis {i+1}: {value:.3f}")

            # Update bar visualization
            bar_width = bar_frame.winfo_width()
            fill_width = bar_width * abs(value) / 2
            fill_frame.configure(width=int(fill_width))

            # Position based on value
            if value >= 0:
                fill_frame.place(relx=0.5, rely=0.5, anchor="w")
            else:
                fill_frame.place(relx=0.5, rely=0.5, anchor="e")

        # Update button states
        for i, label in enumerate(button_labels):
            state = current_selection.get_button(i)
            label.configure(
                text=f"Button {i+1}: {'Pressed' if state else 'Released'}",
                text_color="lime" if state else "red",
            )

    app.after(50, update_joystick_values)


# Poll for joystick connect/disconnect
def poll_pygame_events():
    for event in pygame.event.get():
        if event.type == pygame.JOYDEVICEADDED or event.type == pygame.JOYDEVICEREMOVED:
            update_joysticks(joystick_selector)
    app.after(500, poll_pygame_events)


app.after(50, update_joystick_values)
app.after(50, poll_pygame_events)

app.mainloop()