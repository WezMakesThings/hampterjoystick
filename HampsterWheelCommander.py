# ---
# Wezley Mitchell 2026
# ME412 UKY ITT
# 
# Per University of Kentucky Confidential Disclosure Agreement 5. (2025) Independently 
# developed information is not subject to the CDA.
#
# Distributed under the Filthy Human Hands (FHH) Licence v1.0
# https://whirling.top/fhh/LICENSE.txt
# ---

import platform
import subprocess
import math

# Custom window
import customtkinter as ctk
app = ctk.CTk()
app.geometry("800x600")
app.title("Hampster Mission Control")

# Fixes MAC for some reason
app.update()

# Set theme
import darkdetect

if platform.system().lower() == "linux":
    def theme():
        try:
            cs_out = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                capture_output=True, text=True
            )
            gt_out = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
                capture_output=True, text=True
            )
            if "-dark" in gt_out.stdout.lower() or "-dark" in cs_out.stdout.lower():
                return "Dark"
        except Exception:
            pass
        return "Light"
    darkdetect.theme = theme

ctk.set_appearance_mode(darkdetect.theme().lower())

# Init Pygame
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.init()
pygame.joystick.init()

# Global vars
joystick_refs = []
axis_labels = []
button_labels = []
current_selection = None

# Matlab setup
import matlab.engine
import numpy as np

# Connect 'engine' that is used to pass data to and from matlab.
mtlb = matlab.engine.connect_matlab(background=True)
# Data structure for input axes

# Data structure for output telemetry

# Joystick update Functions
def update_joysticks(js_element: ctk.CTkComboBox, axes_frame, buttons_frame):
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
            joystick_refs[0],
            axes_frame,
            buttons_frame
        )  # Set the first available Joystick as selected, QoL changes planned later
        global current_selection
        current_selection = joystick_refs[0]
        js_element.set(values[0])
        
def setup_joystick_display(joystick, axes_frame, buttons_frame):
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
        axis_container = ctk.CTkFrame(axes_frame, height=10)
        axis_container.pack(fill="x", pady=3, padx=5)
        # axis_container.pack_propagate(False) # Maintain height

        # Bar background frame
        bar_frame = ctk.CTkFrame(
            axis_container, height=10, fg_color="gray20", corner_radius=5
        )
        bar_frame.pack(fill="x", pady=(0, 0))

        # Fill frame for positive/negative indication
        fill_frame = ctk.CTkFrame(
            bar_frame, height=10, fg_color="orange", corner_radius=5, width=0
        )
        fill_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Value label below the bar
        value_label = ctk.CTkLabel(
            axis_container, text=f"Axis {i+1}: 0.000", font=get_scaled_font(), anchor="w"
        )
        value_label.pack(side="left", pady=(2, 0))

        axis_labels.append((bar_frame, fill_frame, value_label))

    # Better Button Indicators
    for i in range(joystick.get_numbuttons()):
        button_frame = ctk.CTkFrame(buttons_frame, fg_color="gray20", height=30, width=30, corner_radius=5)
        button_frame.grid(column=math.floor(i/4), row=i%4, padx=5, pady=5)
        status_label = ctk.CTkLabel(
            button_frame,
            text=f"B{i+1}",
            font=get_scaled_font(),
            text_color="red",
            )
        status_label.pack(pady=1)
        
        button_labels.append(status_label)
        button_frame.pack_propagate(False)
    
    # Button indicators
    #for i in range(joystick.get_numbuttons()):
     #       button_frame = ctk.CTkFrame(buttons_frame, height=5)
      #      button_frame.pack(pady=5, padx=5)
            # button_frame.pack_propagate(False)

       #     status_label = ctk.CTkLabel(
        #        button_frame,
         #       text=f"B{i+1}",
          #      font=get_scaled_font(),
           #     text_color="red",
            #)
            #status_label.pack(pady=1)

            #button_labels.append(status_label)
        
def joystick_selected(choice):
    global current_selection
    if choice and joystick_refs:
        index_str, name = choice.split(": ", 1)
        index = int(index_str) - 1
        if 0 <= index < len(joystick_refs):
            current_selection = joystick_refs[index]
            setup_joystick_display(current_selection)
            
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
                text=f"B{i+1}",
                text_color="lime" if state else "red",
            )

    app.after(50, update_joystick_values)
    
# Poll for joystick connect/disconnect
def poll_pygame_events():
    for event in pygame.event.get():
        if event.type == pygame.JOYDEVICEADDED or event.type == pygame.JOYDEVICEREMOVED:
            update_joysticks(joystick_selector, axes_frame, buttons_frame)
    app.after(500, poll_pygame_events)
            
def main():
    # Main layout
    global joystick_selector
    joystick_selector = ctk.CTkComboBox(app, values=[], command=joystick_selected, variable=ctk.StringVar(value="No Joystick found!"))
    joystick_selector.grid(row=0, column=0, columnspan=2, pady=20, padx=20, sticky="ew")

    global axes_frame, buttons_frame
    axes_frame = ctk.CTkScrollableFrame(app, label_text="Controller Axes")
    axes_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=5)

    buttons_frame = ctk.CTkScrollableFrame(app, label_text="Controller Buttons")
    buttons_frame.grid(row=2, column=0, sticky="nsew", padx=(10, 5), pady=5)
    
    visualizer_frame = ctk.CTkScrollableFrame(app, label_text="Telemetry PLACEHOLDER")
    visualizer_frame.grid(row=1, column=1, sticky="nsew", padx=(5,10), pady=5)
    
    datalogger_frame = ctk.CTkScrollableFrame(app, label_text="Data Logging")
    datalogger_frame.grid(row=2, column=1, sticky="nsew", padx=(5,10), pady=5)

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
    update_joysticks(joystick_selector, axes_frame, buttons_frame)
    app.after(50, update_joystick_values)
    app.after(50, poll_pygame_events)

    app.mainloop()
    
if __name__ == "__main__":
    main()
    # If you forget this line, the program will 'hang' on exit.
    #pygame.quit()