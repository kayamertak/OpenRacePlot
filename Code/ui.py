import tkinter as tk
from tkinter import filedialog, Menu, ttk, simpledialog, messagebox, Canvas, Frame
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.ticker import MaxNLocator
import matplotlib.patches as patches
import random
import os
import sys

from data_import import import_data
from plotting import plot_3d_data, plot_data, add_plot, erase_plot, reset_plots, plot_track_report, plot_scatter_data, plot_histogram_data

class OpenRacePlot:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenRacePlot")
        self.root.state('zoomed')

        self.apply_alt_theme()

        self.current_theme = 'black'
        #self.root.iconbitmap("C:/Users/mcwar/Desktop/Kaya/Data_Vis_Software/Others/OpenRacePlot_Icon.ico")
        icon_path = self.resource_path("C:/Users/mcwar/Desktop/Kaya/Data_Vis_Software/Others/OpenRacePlot_Icon.ico")

        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
        else:
            print("Icon file not found, proceeding without an icon.")
        
        self.dataframes = []
        self.dataset_names = []
        self.dataset_colors = []
        self.channel_names = []
        self.num_plots = 1  # Start with one plot area
        self.is_3d_mode = False

        self.crosshair_lines = []
        self.auto_selected_distance_channel = {}
        self.auto_selected_time_channel = {}
        self.saved_plot_data = []
        self.distance_channels = []
        self.auto_selected_x_channel = {}
        self.channel_to_dataset_map = {}

        self.zoom_pan_callbacks = {}
        self.plot_areas = []  # <-- Initialize plot_areas here
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.create_menu()
        self.create_iconbar()
        self.create_panes()
        self.create_file_explorer()
        self.create_plot_area()  # Ensure plot_frame is created before applying the theme

        # Now apply the black theme after plot_frame is created
        self.set_black_theme()

        # Bind the crosshair event listener on startup
        self.root.bind("<Motion>", self.synchronize_crosshair)

        # Ensure the main window resizes properly
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.panning = False  # Ensure panning and zooming don't conflict
        self.original_xlim = []  # Store original X limits for each axis
        self.original_ylim = []  # Store original Y limits for each axis
        self.panning = False  # Ensure panning and zooming don't conflict
    


    def resource_path(self, relative_path):
        """ Get the absolute path to resource, works for dev and for PyInstaller. """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        
        return os.path.join(base_path, relative_path)

    def synchronize_crosshair(self, event):
        """Synchronize crosshair line across all plots and track its position."""
        try:
            if hasattr(event, 'inaxes') and event.inaxes:
                x_position = event.xdata  # Get the mouse's X position in data coordinates

                # Loop over all subplots and synchronize the crosshair line
                for idx, ax in enumerate(self.axes):
                    if x_position is not None:
                        # If no crosshair exists for this subplot, create it
                        if len(self.crosshair_lines[idx]) == 0:
                            crosshair_line = ax.axvline(x=x_position, color='yellow', linestyle='--')
                            self.crosshair_lines[idx].append(crosshair_line)
                        else:
                            # Update the existing crosshair line
                            self.crosshair_lines[idx][0].set_xdata([x_position])

                # Redraw the canvas to reflect the updated crosshair positions
                self.canvas.draw()

        except Exception as e:
            print(f"Error synchronizing crosshair: {e}")

    def apply_alt_theme(self):
        style = ttk.Style(self.root)
        style.theme_use('clam')

        style.configure('TLabel', background='#333333', foreground='#ffffff')
        style.configure('TButton', background='#444444', foreground='#ffffff', borderwidth=0, padding=6)
        style.map('TButton', background=[('active', '#555555')])
        style.configure('TListbox', background='#333333', foreground='#ffffff')

    def create_menu(self):
        menu_bar = Menu(self.root, tearoff=0, bg='#333333', fg='#ffffff')
        self.root.config(menu=menu_bar)

        file_menu = Menu(menu_bar, tearoff=0, bg='#333333', fg='#ffffff')
        file_menu.add_command(label="Import Data", command=lambda: import_data(self))
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        plot_menu = Menu(menu_bar, tearoff=0, bg='#333333', fg='#ffffff')
        plot_menu.add_command(label="3D Plotting", command=self.open_3d_plot_data_window)
        plot_menu.add_command(label="Scatter Plot", command=lambda: plot_scatter_data(self))
        plot_menu.add_command(label="Histogram Plot", command=lambda: plot_histogram_data(self))
        plot_menu.add_command(label="Track Report", command=lambda: plot_track_report(self))
        menu_bar.add_cascade(label="Plots", menu=plot_menu)

        interface_menu = Menu(menu_bar, tearoff=0, bg='#333333', fg='#ffffff')
        interface_menu.add_command(label="Black Theme", command=self.set_black_theme)
        interface_menu.add_command(label="White Theme", command=self.set_white_theme)
        menu_bar.add_cascade(label="Theme", menu=interface_menu)

        help_menu = Menu(menu_bar, tearoff=0, bg='#333333', fg='#ffffff')
        help_menu.add_command(label="Instructions", command=self.show_instructions)
        help_menu.add_command(label="About")
        menu_bar.add_cascade(label="Help", menu=help_menu)

    def on_closing(self):
        """Handle the closing event to ensure the application shuts down properly."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.quit()  # Stop the main loop
            self.root.destroy()  # Destroy the Tkinter window

    def set_black_theme(self):
        """Switch to black theme and set the current theme to black."""
        self.current_theme = 'black'  # Track the current theme
        self.plot_frame.configure(bg='black')
        self.canvas.get_tk_widget().configure(bg='black')
        self.fig.patch.set_facecolor('black')
        
        for ax in self.axes:
            ax.set_facecolor('black')
            ax.tick_params(colors='white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.title.set_color('white')
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_color('white')
        
        self.canvas.draw()

    def set_white_theme(self):
        """Switch to white theme and set the current theme to white."""
        self.current_theme = 'white'  # Track the current theme
        self.plot_frame.configure(bg='white')
        self.canvas.get_tk_widget().configure(bg='white')
        self.fig.patch.set_facecolor('white')
        
        for ax in self.axes:
            ax.set_facecolor('white')
            ax.tick_params(colors='black')
            ax.xaxis.label.set_color('black')
            ax.yaxis.label.set_color('black')
            ax.title.set_color('black')
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_color('black')
        
        self.canvas.draw()

        
    def open_3d_plot_data_window(self):
        """Opens a window to select data and channels for 3D plotting."""
        # Create the selection window
        select_window = tk.Toplevel(self.root)
        select_window.title("Select Dataset and Channels for 3D Plotting")

        tk.Label(select_window, text="Select Dataset").pack()
        dataset_var = tk.StringVar()
        dataset_menu = ttk.Combobox(select_window, textvariable=dataset_var)
        dataset_menu['values'] = self.dataset_names
        dataset_menu.pack()

        tk.Label(select_window, text="Select X Channel").pack()
        x_var = tk.StringVar()
        x_menu = ttk.Combobox(select_window, textvariable=x_var)
        x_menu.pack()

        tk.Label(select_window, text="Select Y Channel").pack()
        y_var = tk.StringVar()
        y_menu = ttk.Combobox(select_window, textvariable=y_var)
        y_menu.pack()

        tk.Label(select_window, text="Select Z Channel").pack()
        z_var = tk.StringVar()
        z_menu = ttk.Combobox(select_window, textvariable=z_var)
        z_menu.pack()

        def update_channels(event):
            selected_dataset = dataset_var.get()
            if selected_dataset:
                dataset_index = self.dataset_names.index(selected_dataset)
                channels = self.channel_names[dataset_index]
                
                # Display channels without the dataset index
                x_menu['values'] = [ch.split('##')[0] for ch in channels]
                y_menu['values'] = [ch.split('##')[0] for ch in channels]
                z_menu['values'] = [ch.split('##')[0] for ch in channels]

        dataset_menu.bind("<<ComboboxSelected>>", update_channels)

        def plot_3d_selected_channels():
            dataset_name = dataset_var.get()
            x_col = x_var.get()
            y_col = y_var.get()
            z_col = z_var.get()

            if dataset_name and x_col and y_col and z_col:
                # Call the plot_3d_data function from plotting.py, passing selected dataset and channels
                plot_3d_data(self, dataset_name, x_col, y_col, z_col)

            select_window.destroy()

        plot_button = tk.Button(select_window, text="Plot 3D Data", command=plot_3d_selected_channels)
        plot_button.pack(pady=10)

        if self.dataset_names:
            dataset_menu.current(0)
            update_channels(None)


    def clear_plot_area(self):
        for widget in self.plot_frame.winfo_children():
            widget.destroy()
        self.plot_areas = []

    def create_iconbar(self):
        """Create the icon bar with import, plot, and control buttons, styled to match the black theme."""

        # Force-create a style for the iconbar buttons
        style = ttk.Style(self.root)  # Use self.root as a parent
        style.configure(
            'Black.TButton',
            background='#333333',  # Black background
            foreground='#ffffff',  # White text
            borderwidth=1,         # Add a border
            padding=6,
            relief='solid'         # Set relief to 'solid' for visible boundaries
        )
        
        # Change the button appearance when active or pressed
        style.map('Black.TButton',
                background=[('active', '#555555'), ('pressed', '#444444')],  # Darker background when pressed
                relief=[('pressed', 'sunken')])  # Sunken relief when pressed

        # Create the icon bar with a black background
        iconbar = tk.Frame(self.root, bd=1, relief=tk.RAISED, bg='#333333')

        # Use the custom style for all buttons
        import_icon = ttk.Button(iconbar, text="Import", style='Black.TButton', command=lambda: import_data(self))
        import_icon.pack(side=tk.LEFT, padx=2, pady=2)

        plot_icon = ttk.Button(iconbar, text="Plot", style='Black.TButton', command=self.plot_data)
        plot_icon.pack(side=tk.LEFT, padx=2, pady=2)

        add_plot_icon = ttk.Button(iconbar, text="Add Plot", style='Black.TButton', command=self.add_plot)
        add_plot_icon.pack(side=tk.LEFT, padx=2, pady=2)

        erase_plot_icon = ttk.Button(iconbar, text="Erase Plot", style='Black.TButton', command=self.erase_plot)
        erase_plot_icon.pack(side=tk.LEFT, padx=2, pady=2)

        reset_icon = ttk.Button(iconbar, text="Reset", style='Black.TButton', command=self.reset_plots)
        reset_icon.pack(side=tk.LEFT, padx=2, pady=2)

        # Time and Distance buttons on the right side with the same style
        self.distance_button = ttk.Button(iconbar, text="Distance", style='Black.TButton', command=self.activate_distance_mode)
        self.distance_button.pack(side=tk.RIGHT, padx=2, pady=2)

        self.time_button = ttk.Button(iconbar, text="Time", style='Black.TButton', command=self.activate_time_mode)
        self.time_button.pack(side=tk.RIGHT, padx=2, pady=2)

        # Pack the iconbar at the top
        iconbar.pack(side=tk.TOP, fill=tk.X)



    def create_panes(self):
        self.paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg='#333333')
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        self.file_explorer_frame = tk.Frame(self.paned_window, bd=2, relief=tk.SUNKEN, bg='#333333')
        self.paned_window.add(self.file_explorer_frame, minsize=200)

        self.right_frame = tk.Frame(self.paned_window, bg='#333333')
        self.paned_window.add(self.right_frame, stretch="always")

        # Ensure right_frame expands with the window
        self.right_frame.pack_propagate(False)
        self.right_frame.grid_propagate(False)
        self.right_frame.rowconfigure(0, weight=1)
        self.right_frame.columnconfigure(0, weight=1)

    def create_file_explorer(self):
        """Initialize the file explorer (listbox) to show datasets and channels with drag and drop support."""
        file_explorer_frame = tk.Frame(self.file_explorer_frame, bd=2, relief=tk.SUNKEN, bg='#333333')

        self.file_list_label = tk.Label(file_explorer_frame, text="DATA", anchor="w", bg='#333333', fg='#ffffff')
        self.file_list_label.pack(side=tk.TOP, fill=tk.X)

        # Create the listbox to display datasets and channels
        self.file_list = tk.Listbox(file_explorer_frame, bg='#333333', fg='#ffffff', selectbackground='#555555', selectforeground='#ffffff')
        self.file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add a scrollbar if necessary
        scrollbar = tk.Scrollbar(file_explorer_frame, orient="vertical")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_list.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.file_list.yview)

        file_explorer_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Enable dragging functionality for channels
        self.file_list.bind("<Button-1>", self.start_drag)
        self.file_list.bind("<Double-1>", self.toggle_channels)

    def create_plot_area(self):
        """Create or recreate the plot area with subplots based on the number of plot areas."""
        # Clear the right_frame where the figure is displayed
        for widget in self.right_frame.winfo_children():
            widget.destroy()

        # Create a frame to hold the plot areas
        self.plot_frame = tk.Frame(self.right_frame, bg='#333333')
        self.plot_frame.grid(row=0, column=0, sticky="nsew")

        # Create a new figure and subplots, setting the figure size and layout
        self.fig, self.axes = plt.subplots(self.num_plots, 1, figsize=(16, 4 * self.num_plots))

        # Adjust layout between plots
        if self.num_plots > 1:
            self.fig.subplots_adjust(hspace=0)  # Remove vertical space between plots
        else:
            self.fig.subplots_adjust(hspace=0.3)

        # Ensure that even a single subplot is treated as a list
        if self.num_plots == 1:
            self.axes = [self.axes]

        # Create a canvas for the figure and pack it into the plot_frame
        self.canvas = FigureCanvasTkAgg(self.fig, self.plot_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        # Add the toolbar below the plot area
        self.toolbar_frame = tk.Frame(self.plot_frame)
        self.toolbar_frame.grid(row=1, column=0, sticky="ew")
        
        # Create and pack the toolbar inside the toolbar frame
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()

        # Ensure the plot_frame resizes with the window, but toolbar remains in place
        self.plot_frame.grid_rowconfigure(0, weight=1)  # Make sure the plot resizes vertically
        self.plot_frame.grid_columnconfigure(0, weight=1)  # Make sure the plot resizes horizontally

        # Configure grid layout for right_frame to resize properly
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        # Ensure plot frame resizes correctly with window resizing
        self.right_frame.pack_propagate(False)
        self.plot_frame.grid_propagate(False)

        # Initialize crosshair lines for synchronization across all subplots
        self.crosshair_lines = [[] for _ in self.axes]

        # Configure the plot area and the canvas
        for ax in self.axes:
            ax.grid(True, which='major', axis='y', linestyle='--', color='gray', alpha=0.2)

            ax.xaxis.label.set_color('white' if self.set_black_theme else 'black')
            ax.yaxis.label.set_color('white' if self.set_black_theme else 'black')
            ax.tick_params(colors='white' if self.set_black_theme else 'black')
            ax.set_facecolor('black' if self.set_black_theme else 'white')

        # Bind the events for crosshair, zoom, and pan functionality
        self.canvas.mpl_connect("scroll_event", self.zoom_function)
        self.canvas.mpl_connect("button_press_event", self.on_mouse_press)
        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
        self.canvas.mpl_connect("button_release_event", self.on_mouse_release)
        self.canvas.mpl_connect("motion_notify_event", self.synchronize_crosshair)
        self.canvas.draw()

        # Track the plot areas as in the old code
        self.plot_areas = [(self.fig, ax, self.canvas, self.toolbar) for ax in self.axes]

    def on_mouse_press(self, event):
        """Handle mouse press events for panning and right-click context menu."""
        if event.button == 2:  # Middle mouse button (scroll wheel button)
            self.panning = True  # Start panning
            self.x_press = event.x
            self.y_press = event.y
            print("Middle mouse button pressed, starting panning")
        
        elif event.button == 3:  # Right mouse button (context menu)
            # Find which axis (ax) the event occurred in
            if event.inaxes:  # Check if the event occurred inside any axes
                ax = event.inaxes  # Get the axis where the click happened
                # Call the right-click handler and pass the event and axis
                self.on_right_click(event, ax)
            else:
                print("Right click occurred outside any axes")


    def on_mouse_move(self, event):
        """Handle mouse motion to enable pixel-based panning."""
        if self.panning and event.x is not None and event.y is not None:
            dx_pixels = self.x_press - event.x  # Calculate distance moved in pixels (X direction)
            dy_pixels = self.y_press - event.y  # Calculate distance moved in pixels (Y direction)

            for ax in self.axes:
                # Convert pixel movement to data coordinates
                x_lim = ax.get_xlim()
                y_lim = ax.get_ylim()

                # Get axis limits in data coordinates
                ax_pos = ax.get_position()  # Get the plot's position in figure coordinates
                fig_width, fig_height = self.canvas.get_width_height()

                # Calculate data range for X and Y axes
                x_range = x_lim[1] - x_lim[0]
                y_range = y_lim[1] - y_lim[0]

                # Convert pixel movement to data coordinate movement
                dx_data = (dx_pixels / fig_width) * x_range
                dy_data = (dy_pixels / fig_height) * y_range

                # Apply the calculated translation to all plots, synchronizing Y-axis panning
                ax.set_xlim([x_lim[0] + dx_data, x_lim[1] + dx_data])
                ax.set_ylim([y_lim[0] + dy_data, y_lim[1] + dy_data])

            self.canvas.draw()  # Redraw the canvas

    def on_mouse_release(self, event):
        """Handle mouse release to stop panning."""
        if event.button == 2 and self.panning:  # Middle mouse button (mouse wheel button)
            self.panning = False  # Stop panning

    def zoom_function(self, event):
        """Zoom in/out based on the mouse wheel movement."""
        try:
            for ax in self.axes:
                # Get the current axis limits
                cur_xlim = ax.get_xlim()
                cur_ylim = ax.get_ylim()

                # Get the cursor position in data coordinates
                xdata = event.xdata
                ydata = event.ydata

                if xdata is None or ydata is None:
                    return  # Exit if the mouse is outside the plot area

                # Calculate the zoom factor
                zoom_factor = 1.1 if event.button == 'up' else 0.9

                # Set new limits based on cursor position and zoom factor
                new_xlim = [xdata - (xdata - cur_xlim[0]) / zoom_factor,
                            xdata + (cur_xlim[1] - xdata) / zoom_factor]
                new_ylim = [ydata - (ydata - cur_ylim[0]) / zoom_factor,
                            ydata + (cur_ylim[1] - ydata) / zoom_factor]

                # Apply the new limits to the axes
                ax.set_xlim(new_xlim)
                ax.set_ylim(new_ylim)

            # Redraw the canvas to apply the zoom
            self.canvas.draw()

        except Exception as e:
            print(f"Zoom error: {e}")

    def on_right_click(self, event, ax):
        """Handle right-click events to show a context menu based on the number of lines in the plot."""
        if event.button == 3 and event.inaxes == ax:  # Check if right-click occurred inside the axis
            lines = ax.get_lines()  # Get all lines in the current plot

            # Check if there is more than one line in the plot
            if len(lines) > 1:
                # If more than one line, show options to choose between lines
                menu = tk.Menu(self.root, tearoff=0)
                for idx, line in enumerate(lines):
                    line_label = line.get_label()
                    
                    # Create a submenu for each line
                    submenu = tk.Menu(menu, tearoff=0)
                    submenu.add_command(label="Change Line Width", command=lambda l=line: self.change_line_width(l))
                    submenu.add_command(label="Remove Line", command=lambda l=line: self.remove_line(l, ax))
                    
                    menu.add_cascade(label=line_label, menu=submenu)
            else:
                # If only one line, don't ask for which line to modify, directly show options
                menu = tk.Menu(self.root, tearoff=0)
                line = lines[0]
                menu.add_command(label="Change Line Width", command=lambda: self.change_line_width(line))
                menu.add_command(label="Remove Line", command=lambda: self.remove_line(line, ax))
            
            # Convert Matplotlib's event position to Tkinter window coordinates
            widget = self.canvas.get_tk_widget()
            menu_x = widget.winfo_pointerx()
            menu_y = widget.winfo_pointery()
            
            # Display the menu at the mouse position
            menu.post(menu_x, menu_y)
            
    def change_line_width(self, line):
        """Prompt the user to change the line width for the selected line."""
        new_width = simpledialog.askfloat("Change Line Width", "Enter new line width:", minvalue=0.1, maxvalue=10.0)
        if new_width is not None:
            line.set_linewidth(new_width)
            self.canvas.draw()  # Redraw the canvas to apply the changes

    def remove_line(self, line, ax):
        """Remove the selected line from the plot and update the legend."""
        line.remove()  # Remove the line from the axes
        ax.relim()  # Recompute the limits of the plot
        ax.autoscale()  # Rescale the plot to fit the remaining data

        # Remove the line from the legend by refreshing it
        handles, labels = ax.get_legend_handles_labels()  # Get current legend entries
        new_handles_labels = [(h, l) for h, l in zip(handles, labels) if h != line]  # Remove the line from the legend
        new_handles, new_labels = zip(*new_handles_labels) if new_handles_labels else ([], [])
        
        if new_handles:  # If there are still lines remaining, update the legend
            ax.legend(new_handles, new_labels)
        else:
            ax.legend().remove()  # If no lines are left, remove the legend

        self.canvas.draw()  # Redraw the canvas to apply the changes



    def activate_distance_mode(self):
        """Activate the distance mode and highlight the Distance button, re-plotting data if necessary."""
        try:
            # Create a new style for the "Distance" button when it is active
            style = ttk.Style()
            style.configure('Distance.TButton', background='green', foreground='white')

            # Set the button to use this style
            self.distance_button.config(style='Distance.TButton')

            # Reset the time button to the default style
            self.time_button.config(style='TButton')

            # Save the current plot data before switching modes
            print("Saving plot data before switching to distance mode.")
            self.save_plot_data()  # Ensure data is saved


            # Change the x-channel selection logic to use the distance channel
            for dataset_name in self.dataset_names:
                if dataset_name in self.auto_selected_distance_channel:
                    self.auto_selected_x_channel[dataset_name] = self.auto_selected_distance_channel[dataset_name]

            print("Switching to distance mode. Re-plotting with distance as the X-axis.")

            # Reset the plot area and re-plot with the updated X channel
            self.reset_plots()  # Clear the existing plots
            self.restore_plot_data()  # Restore and re-plot with the updated X-channel (distance)

            if self.current_theme == 'black':
                self.set_black_theme()
            else:
                self.set_white_theme()

        except Exception as e:
            print(f"Error activating distance mode: {e}")

    def activate_time_mode(self):
        """Activate the time mode and highlight the Time button, re-plotting data if necessary."""
        try:
            # Create a new style for the "Time" button when it is active
            style = ttk.Style()
            style.configure('Time.TButton', background='blue', foreground='white')

            # Set the button to use this style
            self.time_button.config(style='Time.TButton')

            # Reset the distance button to the default style
            self.distance_button.config(style='TButton')

            # Save the current plot data before switching modes
            print("Saving plot data before switching to time mode.")
            self.save_plot_data()  # Ensure data is saved



            # Change the x-channel selection logic to use the time channel
            for dataset_name in self.dataset_names:
                if dataset_name in self.auto_selected_time_channel:
                    self.auto_selected_x_channel[dataset_name] = self.auto_selected_time_channel[dataset_name]

            print("Switching to time mode. Re-plotting with time as the X-axis.")

            # Reset the plot area and re-plot with the updated X channel
            self.reset_plots()  # Clear the existing plots
            self.restore_plot_data()  # Restore and re-plot with the updated X-channel (time)

            if self.current_theme == 'black':
                self.set_black_theme()
            else:
                self.set_white_theme()

        except Exception as e:
            print(f"Error activating time mode: {e}")



    def replot_with_selected_x_channel(self):
        """Re-plot all data with the selected X channel after switching between distance and time."""
        try:
            for i, ax in enumerate(self.axes):
                ax.clear()  # Clear the axis to reset the plot

                if i < len(self.saved_plot_data):
                    for plot_data in self.saved_plot_data[i]:
                        # Retrieve saved data
                        y_channel, dataset_name, color = plot_data

                        # Select the appropriate X channel (time or distance)
                        x_channel = self.auto_selected_x_channel.get(dataset_name)

                        print(f"Re-plotting with X: {x_channel} and Y: {y_channel} for {dataset_name}")

                        # Find the corresponding dataset
                        dataset_index = self.dataset_names.index(dataset_name)
                        df = self.dataframes[dataset_index]

                        # Ensure both X and Y columns exist in the dataset
                        if x_channel in df.columns and y_channel in df.columns:
                            x_data = pd.to_numeric(df[x_channel], errors="coerce").dropna()
                            y_data = pd.to_numeric(df[y_channel], errors="coerce").dropna()

                            # Check if X and Y data have matching lengths
                            if len(x_data) == len(y_data):
                                ax.plot(x_data, y_data, label=f"{y_channel} vs {x_channel}", color=color)

                                # Update title and x-axis label
                                ax.set_title(f"{y_channel} vs {x_channel}")
                                ax.set_xlabel(x_channel)
                            else:
                                print(f"Skipping due to mismatched lengths: X ({len(x_data)}) and Y ({len(y_data)})")
                        else:
                            print(f"Missing X or Y data for {dataset_name}: X channel: {x_channel}, Y channel: {y_channel}")

                    # Restore legend for the plot
                    ax.legend()

            # Redraw the canvas to update all subplots
            self.canvas.draw()

        except Exception as e:
            print(f"Error re-plotting with new X-axis: {e}")

    def update_plots_x_channel(self, mode):
        """Update the X-axis of all plots based on the mode (Distance/Time)."""
        for i, ax in enumerate(self.axes):
            if i < len(self.saved_plot_data):
                for plot_data in self.saved_plot_data[i]:
                    x_data, y_data, label, color = plot_data

                    # Switch the X-channel based on the current mode
                    if mode == 'Distance':
                        x_channel = self.auto_selected_x_channel.get(self.dataset_names[i], None)
                    else:
                        x_channel = self.auto_selected_time_channel.get(self.dataset_names[i], None)

                    # Update the plot data with the selected X-channel
                    if x_channel in self.dataframes[i].columns:
                        ax.clear()  # Clear the old plot
                        ax.plot(self.dataframes[i][x_channel], y_data, label=label, color=color)

                    # Update X-axis labels and redraw
                    ax.set_xlabel(f"{x_channel} (X-axis)")
                    ax.legend()

        self.canvas.draw()  # Redraw the canvas

    def fit_plots_to_area(self):
        """Set the x-limits of all plot areas based on the limits of the first plot area."""
        if len(self.axes) > 1:
            first_ax = self.axes[0]
            xlim = first_ax.get_xlim()  # Get X-limits of the first plot area

            # Apply the same X-limits to all other plot areas
            for ax in self.axes[1:]:
                ax.set_xlim(xlim)

        self.canvas.draw()  # Redraw the canvas

    def start_drag(self, event):
        """Start dragging the selected channel."""
        widget = event.widget
        selection = widget.curselection()

        if not selection:
            print("No item selected for dragging.")
            return  # Do nothing if no item is selected

        # Get the selected item (the channel name) for dragging
        selected_channel = widget.get(selection[0]).strip("  -").strip()

        print(f"Start dragging channel: {selected_channel}")

        # Check if it's a valid channel (skip dataset names or channel headers)
        if selected_channel.startswith("▶") or selected_channel.startswith("▼") or selected_channel.startswith("⬜"):
            self.drag_data = None  # Invalid drag item
            print("Invalid item selected for dragging.")
        else:
            # Find the dataset name that this channel belongs to
            for i in range(selection[0], -1, -1):
                item_text = widget.get(i).strip("⬜ ")
                if item_text in self.dataset_names:
                    dataset_name = item_text
                    dataset_index = self.dataset_names.index(dataset_name)
                    break
            else:
                print("Dataset not found for this channel.")
                return
            
            # Save the drag data with the dataset name and index
            self.drag_data = f"{dataset_name},{selected_channel},{dataset_index}"

            print(f"Drag data prepared: {self.drag_data}")

            widget.bind("<B1-Motion>", self.do_drag)  # Enable dragging


    def do_drag(self, event):
        """During the drag, highlight the current plot area based on the cursor position."""
        try:
            # Get the plot area under the cursor
            ax = self.get_axis_for_drop(event)

            if ax is not None:
                # Optionally: change the background color or highlight the selected plot area
                for fig, ax, canvas, toolbar in self.plot_areas:
                    ax.set_facecolor('white')  # Reset all axes background
                ax.set_facecolor('lightyellow')  # Highlight the current plot area
                self.canvas.draw()

                # Print to the terminal for debugging
                print(f"Dragging over plot area: {ax}")

            event.widget.bind("<ButtonRelease-1>", self.on_drop)

        except Exception as e:
            print(f"Error determining the plot area during drag: {str(e)}")

    def on_drop(self, event):
        """Handle the drop event and plot the dragged channel."""
        try:
            # Get the dragged data that was set in start_drag
            dropped_data = self.drag_data

            if not dropped_data:
                print("No drag data found for drop.")
                return

            # Extract dataset name, channel name, and dataset index from drag data
            if ',' in dropped_data:
                dataset_name, channel_name, dataset_index = dropped_data.split(',')
                print(f"Dataset: {dataset_name}, Channel: {channel_name}, Dataset Index: {dataset_index}")
            else:
                raise ValueError("Invalid drag data format. Expected 'dataset_name,channel_name,dataset_index'.")

            # Convert dataset_index back to integer
            dataset_index = int(dataset_index)

            # Use the crosshair or another method to determine which axis the data was dropped on
            ax = self.get_axis_for_drop(event)

            if ax is None:
                raise ValueError("Unable to determine the axis for the drop.")

            # Append dataset index to the channel name
            unique_channel_name = f"{channel_name}##{dataset_index}"

            # Plot the dragged channel with the unique channel name
            self.plot_dragged_channel(dataset_name.strip(), unique_channel_name.strip(), ax)

        except ValueError as ve:
            print(f"ValueError occurred: {str(ve)}")
        except Exception as e:
            print(f"An error occurred while handling the drop: {str(e)}")

    def get_axis_for_drop(self, event):
        try:
            # Get the height and width of the measurement area (canvas)
            canvas_height = self.canvas.get_tk_widget().winfo_height()
            canvas_width = self.canvas.get_tk_widget().winfo_width()

            # Get the width of the file explorer or data channel area
            file_explorer_width = self.file_explorer_frame.winfo_width()

            # Adjust the canvas width by excluding the file explorer width
            adjusted_canvas_width = canvas_width + file_explorer_width

            # Get the number of plots (axes)
            num_plots = len(self.axes)

            # Calculate the height for each plot area
            plot_height = canvas_height / num_plots

            # Check if the cursor is within the X boundaries of the measurement area, excluding the data channel area
            if not (file_explorer_width <= event.x <= adjusted_canvas_width):
                print(f"Cursor is outside the measurement area's width (X position: {event.x}, width: {adjusted_canvas_width}).")
                return None

            # Determine which plot area the cursor is over by checking the Y position
            for i, ax in enumerate(self.axes):
                # Calculate the boundaries for this plot area
                top_boundary = i * plot_height
                bottom_boundary = (i + 1) * plot_height

                # Check if the cursor's Y position falls within this plot area's boundaries
                if top_boundary <= event.y <= bottom_boundary:
                    print(f"Cursor is over plot {i + 1} (Y position: {event.y}, top: {top_boundary}, bottom: {bottom_boundary})")
                    return ax  # Return the correct axis for the drop

            print(f"Error: Cursor Y position {event.y} is not over any plot area.")
            return None

        except Exception as e:
            print(f"Error determining drop axis: {str(e)}")
            return None
        

    def plot_dragged_channel(self, dataset_name, unique_channel_name, ax):
        try:
            # Find the dataset index using the dataset name
            dataset_index = next(i for i, d in enumerate(self.dataset_names) if dataset_name in d)

            # Get the dataframe for this dataset
            df = self.dataframes[dataset_index]

            # Check if the auto-selected X channel (distance) is available for this dataset
            x_col = self.auto_selected_x_channel.get(self.dataset_names[dataset_index], None)

            print(f"Auto-selected X channel for dataset {dataset_name}: {x_col}")

            if not x_col:
                # If no distance channel is found, prompt the user for the X-axis channel
                x_col = simpledialog.askstring("X-Axis", "Select X-axis channel for this plot:")
                print("Prompting user for X channel since none was auto-selected.")

            # Ensure the selected X and Y columns exist in the dataframe without the index suffix
            base_channel_name = unique_channel_name.split('##')[0]  # Remove the index suffix

            if x_col not in df.columns:
                raise ValueError(f"X channel '{x_col}' not found in dataset.")

            if base_channel_name not in df.columns:
                raise ValueError(f"Y channel '{base_channel_name}' not found in dataset.")

            # Extract the selected data
            x_data = pd.to_numeric(df[x_col], errors='coerce').dropna()
            y_data = pd.to_numeric(df[base_channel_name], errors='coerce').dropna()

            # Ensure x_data and y_data have matching dimensions
            if len(x_data) != len(y_data):
                print(f"Skipping plot due to mismatched x ({len(x_data)}) and y ({len(y_data)}) dimensions.")
                return  # Skip plotting if dimensions don't match
            
            if self.current_theme == 'black':
                self.set_black_theme()
            else:
                self.set_white_theme()

            # Plot the data on the selected plot area
            ax.plot(x_data, y_data, label=f"{dataset_name}: {base_channel_name} vs {x_col}", color=self.dataset_colors[dataset_index % len(self.dataset_colors)])

            # Set plot title
            ax.set_title(f"{base_channel_name} vs {x_col}")

            # Set X and Y axis labels
            ax.set_xlabel(f"{x_col} (X-axis)")
            ax.set_ylabel(f"{base_channel_name} (Y-axis)")

            # Enable legend if there are labeled artists
            if ax.get_legend_handles_labels()[0]:  # Check if there are any labels to display
                ax.legend()

            # Redraw the canvas
            self.canvas.draw()

        except ValueError as ve:
            print(f"ValueError occurred: {str(ve)}")
        except Exception as e:
            print(f"An error occurred while plotting: {str(e)}")


    def synchronize_zoom_pan(self, source_ax):
        """Ensure zoom/pan syncs across all plots, including zooming to rectangle from the toolbar."""
        try:
            # Get the current limits of the source axis (for synchronization)
            xlim = source_ax.get_xlim()
            ylim = source_ax.get_ylim()

            # Apply these limits to all the other plot areas
            for ax in self.axes:
                if ax != source_ax:
                    ax.set_xlim(xlim)  # Synchronize X-limits
                    ax.set_ylim(ylim)  # Synchronize Y-limits

            # Redraw the canvas after applying limits
            self.canvas.draw()

            # Set callbacks to ensure continuous synchronization for future zoom/pan actions
            for ax in self.axes:
                if ax != source_ax:
                    if ax not in self.zoom_pan_callbacks:
                        # Attach callbacks for future changes
                        xlim_callback_id = ax.callbacks.connect('xlim_changed', lambda *args, ax=ax: self.synchronize_zoom_pan(ax))
                        ylim_callback_id = ax.callbacks.connect('ylim_changed', lambda *args, ax=ax: self.synchronize_zoom_pan(ax))
                        self.zoom_pan_callbacks[ax] = {'xlim': xlim_callback_id, 'ylim': ylim_callback_id}

        except Exception as e:
            print(f"Error while synchronizing zoom/pan: {e}")


    def plot_data(self):
        plot_data(self)

    def add_plot(self):
        """Increase the number of subplots dynamically and retain previous data while fitting all plots."""
        self.save_plot_data()  # Save the current plot data
        
        self.num_plots += 1  # Increase the number of subplots
        
        self.create_plot_area()  # Recreate plot area with the new number of subplots
        
        self.restore_plot_data()  # Restore previous data into the subplots

        # Apply the current theme
        if self.current_theme == 'black':
            self.set_black_theme()
        else:
            self.set_white_theme()

        # Synchronize x-limits of the new plot area with the first plot
        if self.num_plots > 1 and len(self.axes) > 1:
            # Get x-limits of the first plot
            first_ax_xlim = self.axes[0].get_xlim()
            # Set the new plot area's x-limits to match the first plot
            self.axes[-1].set_xlim(first_ax_xlim)
            print(f"Synchronizing x-limits with the first plot: {first_ax_xlim}")

        # After adding the new plot, refit all data in the existing plot areas
        self.refit_all_plots()  # Refit the data into the plot areas

        # Ensure the crosshair is initialized and synchronized across all plots
        self.canvas.mpl_connect("motion_notify_event", self.synchronize_crosshair)

    def refit_all_plots(self):
        """Refit all the data in each plot area after adding or modifying a plot."""
        try:
            for i, ax in enumerate(self.axes):
                # Check if the subplot contains any data
                if len(ax.get_lines()) > 0:
                    # Get all X data across all lines in the current plot
                    all_x_data = np.concatenate([line.get_xdata() for line in ax.get_lines()])
                    all_y_data = np.concatenate([line.get_ydata() for line in ax.get_lines()])
                    
                    # Set new limits that fit all the data
                    ax.set_xlim([all_x_data.min(), all_x_data.max()])
                    ax.set_ylim([all_y_data.min(), all_y_data.max()])

                if self.current_theme == 'black':
                    self.set_black_theme()
                else:
                    self.set_white_theme()
            
            # Redraw the canvas after adjusting the limits
            self.canvas.draw()

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while refitting plots: {str(e)}")

    def save_plot_data(self):
        """Save the current data of all plot areas, ensuring we store only the Y-channel and metadata for later restoration."""
        self.saved_plot_data = []
        for ax in self.axes:  # Loop over all subplots
            plot_data = []
            for line in ax.get_lines():
                y_data = line.get_ydata()  # Save only Y-data
                label = line.get_label()
                color = line.get_color()

                # Extract the dataset name and Y-channel from the label (assuming the format: 'dataset: Y vs X')
                if ':' in label:
                    dataset_name, y_channel_info = label.split(':')
                    y_channel = y_channel_info.split(' vs ')[0].strip()  # Extract Y-channel and strip any spaces
                    plot_data.append((y_channel, dataset_name.strip(), color))  # Save Y-channel, dataset name, and color

            # Save plot title, X-label, and Y-label for restoring later
            title = ax.get_title()
            x_label = ax.get_xlabel()
            y_label = ax.get_ylabel()

            # Append the plot data and metadata (title, labels) for restoration
            self.saved_plot_data.append((plot_data, title, x_label, y_label))

        # Print for debugging
        print(f"Total plot areas saved: {len(self.saved_plot_data)}")
        for i, (plot_data, title, x_label, y_label) in enumerate(self.saved_plot_data):
            print(f"Plot area {i+1} contains {len(plot_data)} plots.")
            for y_channel, dataset_name, color in plot_data:
                print(f"  - Saved Y-channel: {y_channel} from dataset {dataset_name}")
            print(f"  - Title: {title}, X-label: {x_label}, Y-label: {y_label}")


    def restore_plot_data(self):
        """Re-plot the saved Y-channel data using the current X-channel (distance or time) and restore axis labels and titles."""
        try:
            for i, ax in enumerate(self.axes):
                if i < len(self.saved_plot_data):
                    plot_data, title, _, y_label = self.saved_plot_data[i]  # Retrieve saved plot data and labels

                    if not plot_data:
                        continue  # Skip if no plot data is saved for this plot area

                    for y_channel, dataset_name, color in plot_data:
                        # Determine the correct X channel (Distance or Time) based on the current mode
                        x_channel = self.auto_selected_x_channel.get(dataset_name, None)
                        df = self.dataframes[self.dataset_names.index(dataset_name)]

                        if x_channel and y_channel:
                            print(f"Restoring plot with X channel: {x_channel} and Y channel: {y_channel} from dataset {dataset_name}")

                            # Fetch the X and Y data from the dataset
                            x_data = pd.to_numeric(df[x_channel], errors='coerce').dropna()
                            y_data = pd.to_numeric(df[y_channel], errors='coerce').dropna()

                            # Ensure that both X and Y data have the same length before plotting
                            if len(x_data) == len(y_data):
                                ax.plot(x_data, y_data, label=f"{dataset_name}: {y_channel} vs {x_channel}", color=color)

                                # Update the title and x-axis label
                                ax.set_title(f"{y_channel} vs {x_channel}")
                                ax.set_xlabel(x_channel)
                            else:
                                print(f"Skipping plot due to mismatched X and Y dimensions for {y_channel} vs {x_channel}.")
                        else:
                            print(f"Error: Missing X channel or Y channel for {dataset_name}")

                    # Restore the Y-label
                    ax.set_ylabel(y_label)

                    # Restore legend for the plot
                    ax.legend()

            # Redraw the canvas after restoring all plots
            self.canvas.draw()

        except Exception as e:
            print(f"Error while restoring and re-plotting data: {e}")

    def erase_plot(self):
        """Erase the last plot and resize the remaining plots, while retaining the data."""
        try:
            # Ensure there's more than one plot before attempting to erase
            if self.num_plots > 1:
                # Save the current plot data
                self.save_plot_data()

                # Remove the last plot area and destroy its canvas
                fig, ax, canvas, _ = self.plot_areas.pop()
                canvas.get_tk_widget().destroy()

                # Reduce the number of plot areas
                self.num_plots -= 1

                # Recreate the plot area with the remaining plots
                self.create_plot_area()

                # Restore the saved data to the remaining plots
                self.restore_plot_data()

                print(f"Plot erased, {self.num_plots} plots remaining.")

                        # Apply the current theme
                if self.current_theme == 'black':
                    self.set_black_theme()
                else:
                    self.set_white_theme()

            else:
                print("At least one plot area must remain.")

        except Exception as e:
            print(f"Error while erasing plot: {str(e)}")

    def reset_plots(self):
        """Reset the plot areas by clearing the data but keeping the same number of subplots."""
        self.num_plots = len(self.plot_areas)  # Keep the same number of subplots
        self.create_plot_area()  # Recreate the layout with empty subplots
        self.crosshair_lines = [[] for _ in self.axes]  # Reinitialize the crosshair lines for all plot areas

        # Reconnect the crosshair synchronization after reset
        self.canvas.mpl_connect("motion_notify_event", self.synchronize_crosshair)

        print("Plots have been reset, and crosshair functionality has been restored.")
        if self.current_theme == 'black':
            self.set_black_theme()
        else:
            self.set_white_theme()

    def update_file_explorer(self):
        """Update the file explorer with the imported datasets and channels, including lap time."""
        self.file_list.delete(0, tk.END)  # Clear the current list

        for i, dataset_name in enumerate(self.dataset_names):
            # Add the dataset name with its assigned color
            color = self.dataset_colors[i]
            self.file_list.insert(tk.END, f"⬜ {dataset_name}")
            self.file_list.itemconfig(tk.END, {'fg': color})  # Set the color of the dataset

            # Calculate lap time for the dataset
            lap_time = self.calculate_lap_time(i)
            self.file_list.insert(tk.END, f"  Lap Time: {lap_time:.2f} sec")  # Display lap time
            
            # Add the toggleable channels
            self.file_list.insert(tk.END, f"▶ Channels")

            # Track each channel with the corresponding dataset index
            for channel in self.channel_names[i]:
                clean_channel = channel.split("##")[0]  # Strip the '##' part for display
                self.file_list.insert(tk.END, f"  - {clean_channel}")
                self.channel_to_dataset_map[channel] = dataset_name  # Map channel to dataset

    def calculate_lap_time(self, dataset_index):
        """Calculate the lap time from the detected time channel for a given dataset."""
        dataset_name = self.dataset_names[dataset_index]
        time_channel = self.auto_selected_time_channel.get(dataset_name)

        if time_channel:
            df = self.dataframes[dataset_index]
            time_data = pd.to_numeric(df[time_channel], errors='coerce').dropna()

            # Calculate the lap time as the difference between the first and last time values
            lap_time = time_data.iloc[-1] - time_data.iloc[0]
            return lap_time
        return 0.0


    def plot_channel(self, dataset_index, channel_name):
        """Plot a given channel from a dataset."""
        try:
            df = self.dataframes[dataset_index]
            x_channel = self.auto_selected_x_channel.get(dataset_index, None)

            if x_channel and x_channel in df.columns and channel_name in df.columns:
                x_data = df[x_channel]
                y_data = df[channel_name]

                # Plot on the selected plot area (e.g., last created plot area)
                fig, ax, canvas, _ = self.plot_areas[-1]  # Plot on the last plot area
                ax.plot(x_data, y_data, label=f"{channel_name} vs {x_channel}")
                ax.set_xlabel(x_channel)
                ax.set_ylabel(channel_name)
                ax.legend()

                canvas.draw()  # Redraw the canvas to show the new plot

            else:
                messagebox.showerror("Error", f"Channel '{channel_name}' not found in dataset.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while plotting the channel: {str(e)}")

    def toggle_channels(self, event):
        """Handle clicking on the dataset and channels in the file explorer."""
        if not self.file_list.curselection():
            return  # Exit the function if no item is selected

        selected_index = self.file_list.curselection()[0]
        item_text = self.file_list.get(selected_index)

        # Determine if it's a "Channels" line or a dataset line
        if item_text.startswith("▶ Channels") or item_text.startswith("▼ Channels"):
            next_index = selected_index + 1
            if next_index < self.file_list.size() and self.file_list.get(next_index).startswith("  - "):
                # Collapse channels if they are already expanded
                while next_index < self.file_list.size() and self.file_list.get(next_index).startswith("  - "):
                    self.file_list.delete(next_index)
                self.file_list.delete(selected_index)
                self.file_list.insert(selected_index, f"▶ Channels")
            else:
                # Expand channels
                dataset_name_index = selected_index - 1  # This is the line that should contain the dataset name

                # Skip over any lines showing lap times, we only care about the dataset name
                while "Lap Time:" in self.file_list.get(dataset_name_index):
                    dataset_name_index -= 1  # Skip any lap time lines until we reach the dataset name

                dataset_name = self.file_list.get(dataset_name_index).lstrip("⬜").strip()  # Clean symbols before dataset name
                dataset_index = self.dataset_names.index(dataset_name)

                channels = self.channel_names[dataset_index]
                for i, channel in enumerate(channels):
                    clean_channel = channel.split("##")[0]  # Strip the unique number for display
                    self.file_list.insert(selected_index + 1 + i, f"  - {clean_channel}")
                self.file_list.delete(selected_index)
                self.file_list.insert(selected_index, f"▼ Channels")

        # Skip plotting for dataset names or "Toggle Channels" lines
        elif not item_text.startswith("  - "):
            return  # Ignore clicks on dataset names or "Toggle Channels" markers

        else:
            # Extract the dataset and channel names
            dataset_name = self.file_list.get(selected_index - 2).lstrip("⬜").strip()  # Get dataset name two lines above
            channel_name = item_text.strip("  - ")  # Clean the channel name

            dataset_index = self.dataset_names.index(dataset_name)
            df = self.dataframes[dataset_index]

            # Find the corresponding numbered channel in the dataset
            full_channel_name = f"{channel_name}##{dataset_index}"

            if full_channel_name in df.columns:
                self.plot_channel(dataset_index, full_channel_name)
            else:
                print(f"Channel '{full_channel_name}' not found in the dataset.")

    def show_instructions(self):
        # Create a new window for instructions
        instructions_window = tk.Toplevel()
        instructions_window.title("Instructions")

        # Set size of the instructions window, making it a bit larger
        instructions_window.geometry("800x650")

        # Create a frame to hold the text and scrollbar
        text_frame = tk.Frame(instructions_window)
        text_frame.pack(fill=tk.BOTH, expand=True)

        # Create a scrollbar for the instructions window
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create the text widget with word wrapping and bind the scrollbar to it
        instructions_text = tk.Text(
            text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, bg='#333333', fg='white', padx=10, pady=10
        )
        
        instructions_text.insert(tk.END, """
        Welcome to OpenRacePlot!
        
        1. Import Data:
        - Click 'Import' in the File menu or on the icon bar to load your dataset.
        - Supported formats: CSV, Excel, TXT.
        - Make sure channel and data locations are in the same row for successfull data importing
        
        2. Plot Data:
        - After importing, click on a dataset name to see its channels.
        - Drag and drop a channel into the plot area to visualize it.
        - To save the figure in the scene press "S"

        3. Change Plot Settings:
        - Right-click on a plot to change line width or remove a line.
        - Use the 'Distance' or 'Time' buttons to toggle X-axis modes.

        4. 3D, Scatter, and Histogram:
        - Select these options from the 'Plots' menu for specialized visualization.
        
        5. Zoom and Pan:
        - Use the mouse scroll to zoom in/out.
        - Hold the middle mouse button to pan across the plot.
        - Use the navigation toolbar under the plot area to zoom individually in plot areas.

        6. Further Developments and Help
        - Please let me know if you seek any further asistance. mail: kayamertakyurek@gmail.com

        Special thanks to Nicolas Perrin and Edy Garcia from PERRINN and Danny Nowlan from ChassisSIM

        This software developed by Kayamert Akyurek
        """)
        instructions_text.config(state=tk.DISABLED)

        # Attach the scrollbar to the text widget
        scrollbar.config(command=instructions_text.yview)

        # Pack the text widget
        instructions_text.pack(fill=tk.BOTH, expand=True)

    def random_color(self):
        colors = ["Red", "Blue", "Black", "Green"]
        return colors[len(self.dataset_colors) % len(colors)]

if __name__ == "__main__":
    root = tk.Tk()
    app = OpenRacePlot(root)
    root.mainloop()