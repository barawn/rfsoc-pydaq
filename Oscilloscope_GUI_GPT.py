import tkinter as tk
import math

class OscilloscopeGUI:
    def __init__(self, root, data):
        self.root = root
        self.root.title("FPGA Oscilloscope")
        self.width, self.height = 800, 400
        self.data = data  # Static data array (list of lists for multiple channels)

        # Oscilloscope Frame and Canvas
        self.scope_frame = tk.Frame(root, bg="black")
        self.scope_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(self.scope_frame, bg="black", width=self.width, height=self.height)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Control Panel for axis and display options
        self.controls_frame = tk.Frame(root, bg="gray")
        self.controls_frame.pack(fill=tk.X)
        tk.Button(self.controls_frame, text="Auto-Scale", command=self.auto_scale).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(self.controls_frame, text="Clear", command=self.clear_waveform).pack(side=tk.LEFT, padx=5, pady=5)

        # Scaling factors for display
        self.scale_x = self.width / len(self.data[0])  # Horizontal scale based on array length
        self.scale_y = 1.0  # Vertical scaling factor
        self.offset_y = self.height // 2  # Center zero voltage in the middle of the canvas

        # Initial call to scale and draw
        self.auto_scale()  # Adjust scale to fit waveform on the screen
        self.draw_grid()   # Draw dynamic grid based on waveform range
        self.draw_waveform()  # Draw the waveform once

    def draw_grid(self):
        """Draw a dynamic grid with axis labels based on the waveform's min and max values."""
        self.canvas.delete("grid")  # Clear any previous grid lines
        y_ticks = 8  # Number of ticks along the voltage axis

        # Draw horizontal grid lines with dynamic y-axis labels
        for j in range(y_ticks + 1):
            # Calculate grid line position based on dynamic min/max and padding
            y = j * (self.height // y_ticks)
            value = self.max_val - (j / y_ticks) * (self.max_val - self.min_val)
            self.canvas.create_line(0, y, self.width, y, fill="gray", dash=(2, 2), tags="grid")
            self.canvas.create_text(10, y, text=f"{round(value, 1)}", fill="white", anchor=tk.W, tags="grid")

    def draw_waveform(self):
        """Draw the waveform for each channel in the static data array."""
        colors = ["#FF5733", "#33FF57", "#3357FF", "#FF33A1"]

        # Draw each channel
        for ch, channel_data in enumerate(self.data):
            color = colors[ch % len(colors)]
            for i in range(1, len(channel_data)):
                x1, y1 = (i - 1) * self.scale_x, self.offset_y - (channel_data[i - 1] - self.center_val) * self.scale_y
                x2, y2 = i * self.scale_x, self.offset_y - (channel_data[i] - self.center_val) * self.scale_y
                self.canvas.create_line(x1, y1, x2, y2, fill=color, tags="waveform")

    def auto_scale(self):
        """Automatically adjust the scale based on the waveform's min and max, with padding."""
        padding_factor = 0.1  # 10% padding on top and bottom

        # Flatten data and find min and max for scaling
        all_values = [val for ch_data in self.data for val in ch_data]
        if all_values:
            self.max_val = max(all_values)
            self.min_val = min(all_values)
            self.center_val = (self.max_val + self.min_val) / 2  # Center value for zero-point adjustment

            # Apply padding to the min and max values
            range_val = self.max_val - self.min_val
            padded_range = range_val * (1 + 2 * padding_factor)

            # Calculate scale_y to fit the padded range within the canvas
            if padded_range > 0:
                self.scale_y = (self.height / 2) / (padded_range / 2)
            else:
                self.scale_y = 1.0  # Default scale if data is flat

            # Offset to center waveform vertically
            self.offset_y = self.height / 2

        # Redraw the grid and waveform with the updated scale and axis range
        self.canvas.delete("waveform")
        self.draw_grid()
        self.draw_waveform()

    def clear_waveform(self):
        """Clear the waveform from the canvas."""
        self.canvas.delete("waveform")

# Sample static data for 4 channels (e.g., captured from FPGA)
# Replace these lists with actual FPGA data arrays
channel_1 = [50 * math.sin(0.1 * i) for i in range(500)]
channel_2 = [100 if (i // 25) % 2 == 0 else -100 for i in range(500)]
channel_3 = [30 * math.sin(0.15 * i) for i in range(500)]
channel_4 = [(-1)**i * 75 for i in range(500)]  # Square wave
data = [channel_1, channel_2, channel_3, channel_4]

# Run the Oscilloscope GUI with the static data
root = tk.Tk()
app = OscilloscopeGUI(root, data)
root.mainloop()
