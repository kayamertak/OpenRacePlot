import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from tkinter import filedialog, Menu, ttk, simpledialog, messagebox
import tkinter as tk
import numpy as np
from matplotlib.ticker import MaxNLocator

def plot_data(self):
    """Plot data on the selected plot area, auto-selecting the first empty plot area if available."""
    if not self.dataframes or not self.plot_areas:
        messagebox.showerror("Error", "No data imported or no plot areas available.")
        return

    # Create a new window to select dataset and channels for plotting
    select_window = tk.Toplevel(self.root)
    select_window.title("Select Dataset, Plot Area, and Channels")

    tk.Label(select_window, text="Select Dataset").pack(pady=5)
    dataset_var = tk.StringVar()
    dataset_menu = ttk.Combobox(select_window, textvariable=dataset_var)
    dataset_menu['values'] = self.dataset_names
    dataset_menu.pack(pady=5)

    # Automatically detect the first empty plot area or default to the first plot
    def find_empty_plot_area():
        for index, (_, ax, _, _) in enumerate(self.plot_areas):
            if not ax.get_lines():  # Check if the plot area has no lines plotted
                return index
        return 0  # Default to the first plot if all areas are occupied

    empty_plot_area_index = find_empty_plot_area()

    tk.Label(select_window, text="Select Plot Area").pack(pady=5)
    plot_area_var = tk.StringVar(value=f"Plot {empty_plot_area_index + 1}")
    plot_area_menu = ttk.Combobox(select_window, textvariable=plot_area_var)
    plot_area_menu['values'] = [f"Plot {i+1}" for i in range(len(self.plot_areas))]
    plot_area_menu.pack(pady=5)

    tk.Label(select_window, text="Select X Channel").pack(pady=5)
    x_var = tk.StringVar()
    x_menu = ttk.Combobox(select_window, textvariable=x_var)
    x_menu.pack(pady=5)

    tk.Label(select_window, text="Select Y Channel").pack(pady=5)
    y_var = tk.StringVar()
    y_menu = ttk.Combobox(select_window, textvariable=y_var)
    y_menu.pack(pady=5)

    # Update channels when dataset is selected
    def update_channels(event):
        selected_dataset = dataset_var.get()
        if selected_dataset:
            dataset_index = self.dataset_names.index(selected_dataset)
            channels = self.channel_names[dataset_index]

            # Remove the '##dataset_index' part for cleaner display in the dropdown menus
            clean_channels = [channel.split("##")[0] for channel in channels]

            # Populate the channel menus with clean channel names
            x_menu['values'] = clean_channels
            y_menu['values'] = clean_channels

            # Automatically preselect the auto-selected X channel if it exists
            x_channel = self.auto_selected_x_channel.get(selected_dataset, None)
            if x_channel:
                x_menu.set(x_channel.split("##")[0])
            else:
                x_menu.set('')  # Let the user manually choose the X channel

    dataset_menu.bind("<<ComboboxSelected>>", update_channels)

    def plot_selected_channels():
        try:
            dataset_name = dataset_var.get()
            plot_area = plot_area_var.get()
            x_col = x_var.get()
            y_col = y_var.get()

            if dataset_name and plot_area and x_col and y_col:
                dataset_index = self.dataset_names.index(dataset_name)
                df = self.dataframes[dataset_index]

                # Check if the selected X and Y columns exist in the dataset
                full_x_col = x_col if x_col in df.columns else None
                full_y_col = y_col if y_col in df.columns else None

                if not full_x_col or not full_y_col:
                    messagebox.showerror("Error", f"Invalid channels: {x_col}, {y_col}")
                    return

                # Extract the selected data using the full channel names
                x_data = pd.to_numeric(df[full_x_col], errors='coerce').dropna()
                y_data = pd.to_numeric(df[full_y_col], errors='coerce').dropna()

                # Check if there's valid data
                if len(x_data) == 0 or len(y_data) == 0:
                    messagebox.showerror("Error", "Selected channels contain no valid data.")
                    return

                # Select the correct plot area
                plot_area_index = int(plot_area.split()[1]) - 1
                fig, ax, canvas, toolbar = self.plot_areas[plot_area_index]

                # Clear the existing plot in the selected plot area
                ax.clear()

                # Store the min and max values for clamping panning and zooming
                self.x_min, self.x_max = x_data.min(), x_data.max()
                self.y_min, self.y_max = y_data.min(), y_data.max()

                # Plot the data on the selected plot area
                ax.plot(x_data, y_data, label=f"{y_col} vs {x_col}", color=self.dataset_colors[dataset_index])

                # Set title, labels, and legend
                ax.set_title(f"{y_col} vs {x_col}")
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)
                ax.legend()

                # Adjust x-axis and y-axis ticks to avoid overlap
                ax.xaxis.set_major_locator(MaxNLocator(nbins=10))  # Limit the number of x-axis ticks
                ax.yaxis.set_major_locator(MaxNLocator(nbins=10))  # Limit the number of y-axis ticks

                # Set the new x-axis limits to the new x_data range
                ax.set_xlim([x_data.min(), x_data.max()])
                ax.set_ylim([y_data.min(), y_data.max()])

                # Redraw the canvas
                canvas.draw()

                # Save the plot data after plotting so that it can be restored
                self.save_plot_data()

                # Ensure crosshair synchronization is set up after plotting
                self.crosshair_lines = [[] for _ in self.axes]
                self.canvas.mpl_connect("motion_notify_event", self.synchronize_crosshair)

                select_window.destroy()

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    plot_button = tk.Button(select_window, text="Plot", command=plot_selected_channels)
    plot_button.pack(pady=10)

    if self.dataset_names:
        dataset_menu.current(0)
        update_channels(None)


def add_plot(app):
    app.num_plots += 1
    old_plots = app.plots
    app.plots = [[] for _ in range(app.num_plots)]

    app.figure.clear()
    app.figure, app.ax = plt.subplots(app.num_plots, 1, figsize=(15, 7 * app.num_plots))

    if isinstance(app.ax, np.ndarray):
        for i, ax in enumerate(app.ax):
            if i < len(old_plots):
                for plot in old_plots[i]:
                    ax.plot(plot[0], plot[1], label=plot[2], color=plot[3])
                    ax.set_xlabel(plot[4])
                ax.set_title(f"Plot {i+1}")
                ax.set_ylabel("Y-axis")
                ax.legend()
    else:
        # If only one plot remains
        for plot in old_plots[0]:
            app.ax.plot(plot[0], plot[1], label=plot[2], color=plot[3])
            app.ax.set_xlabel(plot[4])
        app.ax.set_title("Plot 1")
        app.ax.set_ylabel("Y-axis")
        app.ax.legend()

    app.canvas.figure = app.figure
    app.canvas.draw()
    app.toolbar.update()

def erase_plot(app):
    if app.num_plots > 1:
        app.num_plots -= 1
        old_plots = app.plots[:app.num_plots]
        app.plots = old_plots

        app.figure.clear()
        app.figure, app.ax = plt.subplots(app.num_plots, 1, figsize=(15, 7 * app.num_plots))

        if isinstance(app.ax, np.ndarray):
            for i, ax in enumerate(app.ax):
                for plot in old_plots[i]:
                    ax.plot(plot[0], plot[1], label=plot[2], color=plot[3])
                    ax.set_xlabel(plot[4])
                ax.set_title(f"Plot {i+1}")
                ax.set_ylabel("Y-axis")
                ax.legend()
        else:
            # If only one plot remains
            for plot in old_plots[0]:
                app.ax.plot(plot[0], plot[1], label=plot[2], color=plot[3])
                app.ax.set_xlabel(plot[4])
            app.ax.set_title("Plot 1")
            app.ax.set_ylabel("Y-axis")
            app.ax.legend()

        app.canvas.figure = app.figure
        app.canvas.draw()
        app.toolbar.update()

def reset_plots(app):
    if isinstance(app.ax, list):
        # If ax is a list (multiple plots)
        for ax in app.ax:
            ax.clear()
    elif isinstance(app.ax, np.ndarray):
        # If ax is an ndarray (multiple plots as an array)
        for ax in app.ax.flatten():
            ax.clear()
    else:
        # If ax is a single Axes object (one plot)
        app.ax.clear()

    app.plots = [[] for _ in range(app.num_plots)]
    app.canvas.draw()


def plot_track_report(app):
    """Function to handle the track report plotting."""
    if not app.dataframes or not app.plot_areas:
        messagebox.showerror("Error", "No data imported or no plot areas available.")
        return

    # Create a new window for track report plotting
    select_window = tk.Toplevel(app.root)
    select_window.title("Select Dataset and Channels for Track Report")

    tk.Label(select_window, text="Select Dataset").pack(pady=5)
    dataset_var = tk.StringVar()
    dataset_menu = ttk.Combobox(select_window, textvariable=dataset_var)
    dataset_menu['values'] = app.dataset_names
    dataset_menu.pack(pady=5)

    tk.Label(select_window, text="Select Plot Area").pack(pady=5)
    plot_area_var = tk.StringVar()
    plot_area_menu = ttk.Combobox(select_window, textvariable=plot_area_var)
    plot_area_menu['values'] = [f"Plot {i+1}" for i in range(len(app.plot_areas))]
    plot_area_menu.pack(pady=5)

    tk.Label(select_window, text="Select Position X Channel").pack(pady=5)
    x_var = tk.StringVar()
    x_menu = ttk.Combobox(select_window, textvariable=x_var)
    x_menu.pack(pady=5)

    tk.Label(select_window, text="Select Position Y Channel").pack(pady=5)
    y_var = tk.StringVar()
    y_menu = ttk.Combobox(select_window, textvariable=y_var)
    y_menu.pack(pady=5)

    tk.Label(select_window, text="Select Throttle Channel").pack(pady=5)
    throttle_var = tk.StringVar()
    throttle_menu = ttk.Combobox(select_window, textvariable=throttle_var)
    throttle_menu.pack(pady=5)

    def update_channels(event):
        selected_dataset = dataset_var.get()
        if selected_dataset:
            dataset_index = app.dataset_names.index(selected_dataset)
            channels = app.channel_names[dataset_index]
            x_menu['values'] = [ch.split('##')[0] for ch in channels]
            y_menu['values'] = [ch.split('##')[0] for ch in channels]
            throttle_menu['values'] = [ch.split('##')[0] for ch in channels]

    dataset_menu.bind("<<ComboboxSelected>>", update_channels)

    def plot_track_selected_channels():
        try:
            dataset_name = dataset_var.get()
            x_col = x_var.get()
            y_col = y_var.get()
            throttle_col = throttle_var.get()
            plot_area = plot_area_var.get()

            if dataset_name and plot_area and x_col and y_col and throttle_col:
                dataset_index = app.dataset_names.index(dataset_name)
                df = app.dataframes[dataset_index]

                # Clean the column names without dataset index
                clean_x_col = x_col.split('##')[0]
                clean_y_col = y_col.split('##')[0]
                clean_throttle_col = throttle_col.split('##')[0]

                if clean_x_col not in df.columns or clean_y_col not in df.columns or clean_throttle_col not in df.columns:
                    messagebox.showerror("Error", "Selected channels not found in dataset.")
                    return

                # Extract the selected data
                x_data = pd.to_numeric(df[clean_x_col], errors='coerce').dropna()
                y_data = pd.to_numeric(df[clean_y_col], errors='coerce').dropna()
                throttle_data = pd.to_numeric(df[clean_throttle_col], errors='coerce').dropna()

                if len(x_data) == 0 or len(y_data) == 0 or len(throttle_data) == 0:
                    messagebox.showerror("Error", "Selected channels contain no valid data.")
                    return

                # Select the correct plot area
                plot_area_index = int(plot_area.split()[1]) - 1
                fig, ax, canvas, toolbar = app.plot_areas[plot_area_index]

                # Normalize the throttle data for color mapping
                norm = plt.Normalize(throttle_data.min(), throttle_data.max())
                colormap = plt.cm.coolwarm

                # Clear the existing plot in the selected plot area
                ax.clear()

                # Plot the track with throttle as the colormap
                scatter = ax.scatter(x_data, y_data, c=throttle_data, cmap=colormap, norm=norm, label=f"Throttle: {clean_throttle_col}")

                # Set axis labels and title
                ax.set_xlabel(clean_x_col)
                ax.set_ylabel(clean_y_col)
                ax.set_title(f"Track Report: {clean_y_col} vs {clean_x_col}")

                # Check the current theme and apply corresponding text colors
                if app.current_theme == 'black':
                    ax.xaxis.label.set_color('white')
                    ax.yaxis.label.set_color('white')
                    ax.title.set_color('white')
                    ax.tick_params(colors='white')  # Set the color of the ticks and tick labels to white
                else:
                    ax.xaxis.label.set_color('black')
                    ax.yaxis.label.set_color('black')
                    ax.title.set_color('black')
                    ax.tick_params(colors='black')  # Set the color of the ticks and tick labels to black

                # Add colorbar for throttle
                cbar = plt.colorbar(scatter, ax=ax)
                cbar.set_label(clean_throttle_col)
                if app.current_theme == 'black':
                    cbar.ax.yaxis.set_tick_params(color='white')  # Change the color of the colorbar tick marks
                    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')  # Change the color of the colorbar labels

                # Redraw the canvas
                canvas.draw()
                select_window.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            print(f"Error during track plotting: {e}")

    plot_button = tk.Button(select_window, text="Plot Track Report", command=plot_track_selected_channels)
    plot_button.pack(pady=10)

    if app.dataset_names:
        dataset_menu.current(0)
        update_channels(None)


def plot_3d_data(app, dataset_name, x_col, y_col, z_col):
    """Function to handle 3D plotting in a new window."""
    if not app.dataframes or not app.plot_areas:
        messagebox.showerror("Error", "No data imported or no plot areas available.")
        return

    try:
        # Find the index of the selected dataset
        dataset_index = app.dataset_names.index(dataset_name)
        df = app.dataframes[dataset_index]

        # Ensure that the selected columns exist in the DataFrame
        if x_col not in df.columns or y_col not in df.columns or z_col not in df.columns:
            messagebox.showerror("Error", "Selected channels not found in the dataset.")
            return

        # Convert the selected columns to numeric, forcing non-numeric values to NaN
        x_data = pd.to_numeric(df[x_col], errors='coerce').dropna()
        y_data = pd.to_numeric(df[y_col], errors='coerce').dropna()
        z_data = pd.to_numeric(df[z_col], errors='coerce').dropna()

        # Check if there's any invalid (non-numeric) data in the columns
        if x_data.empty or y_data.empty or z_data.empty:
            messagebox.showerror("Error", "Selected channels contain no valid numeric data.")
            return

        # Normalize the Z data for the colormap
        norm = plt.Normalize(z_data.min(), z_data.max())
        colormap = plt.cm.coolwarm  # Choose colormap from blue to red

        # Create a new window for the 3D plot
        plot_window = tk.Toplevel(app.root)
        plot_window.title("3D Plot Viewer")

        # Create a new figure and 3D axis
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(111, projection='3d')

        # Plot the 3D scatter plot with colormap
        scatter = ax.scatter(x_data, y_data, z_data, c=z_data, cmap=colormap, norm=norm)

        # Set axis labels and title
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_zlabel(z_col)
        ax.set_title(f"3D Scatter Plot of {z_col} vs {y_col} vs {x_col}")

        # Add color bar for the colormap
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label(z_col)

        # Embed the plot in the new window using FigureCanvasTkAgg
        canvas = FigureCanvasTkAgg(fig, plot_window)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Add the navigation toolbar to the window
        toolbar = NavigationToolbar2Tk(canvas, plot_window)
        toolbar.update()

        # Redraw the canvas
        canvas.draw()

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

def plot_scatter_data(app):
    """Function to handle Scatter plotting."""
    if not app.dataframes or not app.plot_areas:
        messagebox.showerror("Error", "No data imported or no plot areas available.")
        return

    # Create a new window to select dataset and channels for Scatter plotting
    select_window = tk.Toplevel(app.root)
    select_window.title("Select Dataset and Channels for Scatter Plotting")

    tk.Label(select_window, text="Select Dataset").pack(pady=5)
    dataset_var = tk.StringVar()
    dataset_menu = ttk.Combobox(select_window, textvariable=dataset_var)
    dataset_menu['values'] = app.dataset_names
    dataset_menu.pack(pady=5)

    tk.Label(select_window, text="Select Plot Area").pack(pady=5)
    plot_area_var = tk.StringVar()
    plot_area_menu = ttk.Combobox(select_window, textvariable=plot_area_var)
    plot_area_menu['values'] = [f"Plot {i+1}" for i in range(len(app.plot_areas))]
    plot_area_menu.pack(pady=5)

    tk.Label(select_window, text="Select X Channel").pack(pady=5)
    x_var = tk.StringVar()
    x_menu = ttk.Combobox(select_window, textvariable=x_var)
    x_menu.pack(pady=5)

    tk.Label(select_window, text="Select Y Channel").pack(pady=5)
    y_var = tk.StringVar()
    y_menu = ttk.Combobox(select_window, textvariable=y_var)
    y_menu.pack(pady=5)

    def update_channels(event):
        selected_dataset = dataset_var.get()
        if selected_dataset:
            dataset_index = app.dataset_names.index(selected_dataset)
            channels = app.channel_names[dataset_index]
            print(f"Available channels in dataset {selected_dataset} (index {dataset_index}): {channels}")

            # Populate X and Y channel menus without the dataset index for display
            x_menu['values'] = [ch.split('##')[0] for ch in channels]
            y_menu['values'] = [ch.split('##')[0] for ch in channels]

    dataset_menu.bind("<<ComboboxSelected>>", update_channels)

    def plot_selected_scatter_channels():
        try:
            dataset_name = dataset_var.get()
            x_col = x_var.get()
            y_col = y_var.get()
            plot_area = plot_area_var.get()

            print(f"Selected dataset: {dataset_name}")
            print(f"Selected X channel: {x_col}")
            print(f"Selected Y channel: {y_col}")
            print(f"Selected plot area: {plot_area}")

            if dataset_name and x_col and y_col and plot_area:
                dataset_index = app.dataset_names.index(dataset_name)
                df = app.dataframes[dataset_index]

                print(f"Dataset index: {dataset_index}")
                print(f"Available columns in dataset: {df.columns.tolist()}")

                # Use cleaned column names without the dataset index
                clean_x_col = x_col.split('##')[0]
                clean_y_col = y_col.split('##')[0]

                print(f"Clean X channel: {clean_x_col}")
                print(f"Clean Y channel: {clean_y_col}")

                if clean_x_col not in df.columns or clean_y_col not in df.columns:
                    messagebox.showerror("Error", f"Selected channels not found in dataset: {x_col}, {y_col}")
                    print(f"X channel {clean_x_col} or Y channel {clean_y_col} not found in dataframe columns: {df.columns.tolist()}")
                    return

                # Extract the selected data
                x_data = pd.to_numeric(df[clean_x_col], errors='coerce').dropna()
                y_data = pd.to_numeric(df[clean_y_col], errors='coerce').dropna()

                print(f"X data length: {len(x_data)}, Y data length: {len(y_data)}")

                # Select the correct plot area
                plot_area_index = int(plot_area.split()[1]) - 1
                ax = app.plot_areas[plot_area_index][1]

                # Plot the scatter data on the selected plot area (don't clear the existing plots)
                scatter = ax.scatter(x_data, y_data, label=f"{y_col} vs {x_col}", color=app.dataset_colors[dataset_index])

                # Set labels, title, and legend
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)
                ax.set_title(f"Scatter Plot of {y_col} vs {x_col}")
                ax.legend()

                # Redraw the canvas
                app.plot_areas[plot_area_index][2].draw()
                select_window.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            print(f"Error during scatter plotting: {e}")

    plot_button = tk.Button(select_window, text="Plot Scatter", command=plot_selected_scatter_channels)
    plot_button.pack(pady=10)

    if app.dataset_names:
        dataset_menu.current(0)
        update_channels(None)

def plot_histogram_data(app):
    """Function to handle Histogram plotting."""
    if not app.dataframes or not app.plot_areas:
        messagebox.showerror("Error", "No data imported or no plot areas available.")
        return

    # Create a new window to select dataset and channels for Histogram plotting
    select_window = tk.Toplevel(app.root)
    select_window.title("Select Dataset and Damper Speeds for 4 Tires")

    tk.Label(select_window, text="Select Dataset").pack(pady=5)
    dataset_var = tk.StringVar()
    dataset_menu = ttk.Combobox(select_window, textvariable=dataset_var)
    dataset_menu['values'] = app.dataset_names
    dataset_menu.pack(pady=5)

    # Assume damper speed channels for 4 tires are predefined in the dataset
    tire_dampers = {
        "Front Left": tk.StringVar(),
        "Front Right": tk.StringVar(),
        "Rear Left": tk.StringVar(),
        "Rear Right": tk.StringVar()
    }

    # Create a combobox for each tire to select the damper speed channels
    damper_menus = {}
    for tire, var in tire_dampers.items():
        tk.Label(select_window, text=f"Select {tire} Damper Speed").pack(pady=5)
        damper_menu = ttk.Combobox(select_window, textvariable=var)
        damper_menu.pack(pady=5)
        damper_menus[tire] = damper_menu  # Save the menu for each tire

    def update_channels(event):
        selected_dataset = dataset_var.get()
        if selected_dataset:
            dataset_index = app.dataset_names.index(selected_dataset)
            channels = app.channel_names[dataset_index]
            # Update all tire damper speed comboboxes with the channel names
            for tire, damper_menu in damper_menus.items():
                damper_menu['values'] = [ch.split('##')[0] for ch in channels]  # Strip dataset index

    dataset_menu.bind("<<ComboboxSelected>>", update_channels)

    def plot_histogram_2x2():
        try:
            dataset_name = dataset_var.get()
            if dataset_name:
                dataset_index = app.dataset_names.index(dataset_name)
                df = app.dataframes[dataset_index]

                # Prepare the plot in a 2x2 layout
                if not hasattr(app, 'histogram_tab') or not app.histogram_tab.winfo_exists():
                    app.histogram_tab = tk.Toplevel(app.root)
                    app.histogram_tab.title("Histogram Plot - 4 Tires (2x2)")

                    app.histogram_fig, app.histogram_axes = plt.subplots(2, 2, figsize=(12, 8))
                    app.histogram_canvas = FigureCanvasTkAgg(app.histogram_fig, app.histogram_tab)
                    app.histogram_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
                    app.histogram_toolbar = NavigationToolbar2Tk(app.histogram_canvas, app.histogram_tab)
                    app.histogram_toolbar.pack(side=tk.TOP, fill=tk.X)
                    app.histogram_canvas.draw()

                # Get the selected channels and plot them in the 2x2 grid
                for i, (tire, var) in enumerate(tire_dampers.items()):
                    ax = app.histogram_axes[i // 2, i % 2]
                    damper_channel = var.get()

                    # Use cleaned channel names for titles and legends
                    clean_damper_channel = damper_channel.split('##')[0] if damper_channel else None

                    if clean_damper_channel not in df.columns:
                        messagebox.showerror("Error", f"Invalid channel: {damper_channel}")
                        return

                    # Extract data for histogram plotting
                    damper_data = pd.to_numeric(df[clean_damper_channel], errors='coerce').dropna()

                    # Plot the histogram for the selected damper channel
                    ax.clear()
                    ax.hist(damper_data, bins=30, color=app.dataset_colors[dataset_index], edgecolor="black", alpha=0.7)

                    # Set title and labels based on the selected channels
                    ax.set_title(f"{clean_damper_channel}")
                    ax.set_xlabel(f"{clean_damper_channel}")
                    ax.set_ylabel('Frequency')

                    # Limit the ticks to avoid overlap
                    ax.xaxis.set_major_locator(MaxNLocator(nbins=10))  # Limit the number of x-axis ticks

                # Call tight_layout to ensure no overlap between subplots
                plt.tight_layout()

                # Redraw the canvas
                app.histogram_canvas.draw()

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            print(f"Error during histogram plotting: {e}")

    plot_button = tk.Button(select_window, text="Plot 4-Tire Histogram", command=plot_histogram_2x2)
    plot_button.pack(pady=10)

    if app.dataset_names:
        dataset_menu.current(0)
        update_channels(None)

