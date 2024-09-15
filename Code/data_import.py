import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import uuid  # Import to generate unique IDs


colors = ["Red", "Blue", "Black", "Green"]

def import_data(self):
    """Import data from a file and detect distance- and time-related channels."""
    try:
        # Ask the user for the file to import
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"), ("Excel Files", "*.xlsx"), ("Text Files", "*.txt")])
        if not file_path:
            return  # Exit if no file is selected

        # Detect file type and read accordingly
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif file_path.endswith('.TXT'):
            df = pd.read_csv(file_path, delimiter="\t", header=3, skiprows=[4], on_bad_lines='skip')  # Adjust as needed
        else:
            raise ValueError("Unsupported file type")

        # Add the dataframe to the list of imported data
        self.dataframes.append(df)

        # Extract dataset name and assign it to the dataset list
        dataset_name = file_path.split('/')[-1]  # Use the file name as the dataset name
        self.dataset_names.append(dataset_name)

        # Extract channel names (columns) and modify them to include dataset index using the '##' delimiter
        dataset_index = len(self.dataframes) - 1  # The current dataset's index

        modified_channels = [f"{channel}##{dataset_index}" for channel in df.columns]  # Append dataset index with '##'
        self.channel_names.append(modified_channels)  # Store modified channel names

        # Apply the current theme
        if self.current_theme == 'black':
            self.set_black_theme()
        else:
            self.set_white_theme()

        # Map each channel (with '##' index) to its dataset
        for channel in modified_channels:
            self.channel_to_dataset_map[channel] = dataset_name

        # Detect distance-related channels and store them
        distance_related_keywords = ["dist", "xdist", "distance", "Distance"]
        detected_distance_channel = None
        for channel in df.columns:
            if any(keyword in channel.lower() for keyword in distance_related_keywords):
                detected_distance_channel = channel
                print(f"Detected distance channel: {detected_distance_channel}")
                break

        # Detect time-related channels and store them
        time_related_keywords = ["time", "timestamp", "Time", "Timestamp", "xTime"]
        detected_time_channel = None
        for channel in df.columns:
            if any(keyword in channel.lower() for keyword in time_related_keywords):
                detected_time_channel = channel
                print(f"Detected time channel: {detected_time_channel}")
                break

        # Store the detected distance and time channels for auto-selection
        self.auto_selected_distance_channel[dataset_name] = detected_distance_channel
        self.auto_selected_time_channel[dataset_name] = detected_time_channel

        # Assign a random color for each dataset for plotting purposes
        dataset_color = self.random_color()
        self.dataset_colors.append(dataset_color)

        # Update the file explorer to show the dataset and its channels
        self.update_file_explorer()

        # Automatically activate distance mode by default if a distance channel is found
        if detected_distance_channel:
            print(f"Activating distance mode for {dataset_name}")
            self.activate_distance_mode()
        elif detected_time_channel:
            print(f"Activating time mode for {dataset_name}")
            self.activate_time_mode()  # Activate time mode if no distance channel is found but time is

        print(f"Data imported successfully from {dataset_name}. Channels: {modified_channels}")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while importing data: {str(e)}")
        print(f"Error during import: {str(e)}")


def import_csv(app, file_path):
    try:
        print(f"Reading CSV file: {file_path}")
        df = pd.read_csv(file_path, skiprows=[1])
        append_data(app, df, file_path)
    except Exception as e:
        print(f"Exception occurred while importing {file_path}: {str(e)}")
        messagebox.showerror("Error", f"Failed to import {file_path}: {str(e)}")

def import_xlsx(app, file_path):
    try:
        print(f"Reading Excel file: {file_path}")
        df = pd.read_excel(file_path)
        append_data(app, df, file_path)
    except Exception as e:
        print(f"Exception occurred while importing {file_path}: {str(e)}")
        messagebox.showerror("Error", f"Failed to import {file_path}: {str(e)}")

def import_txt(app, file_path):
    try:
        print(f"Reading TXT file: {file_path}")
        df = pd.read_csv(file_path, sep='\t', header=3, on_bad_lines='skip')
        print(f"Data imported successfully with shape: {df.shape}")
        print(df.head())  # Print the first few rows of the dataframe
        append_data(app, df, file_path)
    except Exception as e:
        print(f"Exception occurred while importing {file_path}: {str(e)}")
        messagebox.showerror("Error", f"Failed to import {file_path}: {str(e)}")

def append_data(app, df, file_path):
    app.dataframes.append(df)
    dataset_name = file_path.split("/")[-1]
    color_index = len(app.dataset_names) % len(colors)
    color = colors[color_index]
    app.dataset_names.append(dataset_name)
    app.dataset_colors.append(color)
    index = app.file_list.size()
    app.file_list.insert(tk.END, f"⬜ {dataset_name}")
    app.file_list.itemconfig(index, foreground=color)
    app.file_list.insert(tk.END, "▶ Channels:")
    for channel in df.columns.tolist():
        app.file_list.insert(tk.END, f"  - {channel}")
    app.channel_names.append(df.columns.tolist())
