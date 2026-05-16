import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import List, Optional, Tuple, Union, Dict
import os

def create_diverging_bar_chart(
    data: Dict[str, List[float]],  # Dictionary mapping group names to their counts
    labels: List[str],
    output_path: str,
    title: Optional[str] = None,
    x_label: str = "Percentage (%)",
    y_label: Optional[str] = None,
    width: float = 10,
    height: float = 5,
    zoom_factor: float = 1.0,
    color_map: str = 'coolwarm_r',
    color_range: Tuple[float, float] = (0.15, 0.85)
) -> None:
    """
    Create a diverging bar chart with multiple groups of data.
    
    Args:
        data: Dictionary mapping group names to their counts/percentages
              e.g. {"Group A": [10, 20, 30], "Group B": [15, 25, 35]}
        labels: List of labels for each bar segment, in order from most negative to most positive
               e.g. ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]
        output_path: Full path where to save the output file (with or without .png extension)
                    Can be just a filename (e.g. "chart.png") or a full path (e.g. "output/chart.png")
        title: Optional title for the plot
        x_label: Label for the x-axis (default: "Percentage (%)")
        y_label: Optional label for the y-axis
        width: Width of the plot in inches
        height: Height of the plot in inches
        zoom_factor: Factor to scale the figure dimensions
        color_map: Name of the matplotlib colormap to use
        color_range: Tuple of (start, end) values for the colormap range
    
    Returns:
        None. Saves the plot to the specified output path.
    """
    # Input validation
    if not data:
        raise ValueError("No data provided")
    if not all(len(counts) == len(labels) for counts in data.values()):
        raise ValueError("All groups must have the same number of categories as labels")
    
    # Ensure output path has .png extension
    if not output_path.lower().endswith('.png'):
        output_path += '.png'
    
    # Create output directory if it doesn't exist (only if path contains directories)
    output_dir = os.path.dirname(output_path)
    if output_dir:  # Only create directory if path contains directories
        os.makedirs(output_dir, exist_ok=True)
    
    # Convert inputs to numpy arrays
    labels = np.array(labels)
    group_names = list(data.keys())
    counts = np.array(list(data.values()))
    
    # Generate colors dynamically based on original category order
    n_categories = len(labels)
    category_colors = plt.get_cmap(color_map)(np.linspace(color_range[0], color_range[1], n_categories))
    
    # Reorder data for diverging chart display
    middle_index = n_categories // 2
    
    if n_categories % 2 == 1:  # Odd number of categories (with neutral)
        neutral_value = counts[:, middle_index] / 2  # Split neutral into two parts
        neutral_color = category_colors[middle_index]
        
        # Create the new order: [Neutral_left, Disagree, Strongly Disagree | Strongly Agree, Agree, Neutral_right]
        reordered_counts = np.column_stack([
            neutral_value,                    # Left half of neutral
            counts[:, 1:middle_index],        # Disagree
            counts[:, 0:1],                   # Strongly Disagree
            counts[:, -1:],                   # Strongly Agree
            counts[:, middle_index+1:-1],     # Agree
            neutral_value                     # Right half of neutral
        ])
        
        # Reorder colors accordingly
        reordered_colors = np.vstack([
            neutral_color,                    # Left half of neutral
            category_colors[1:middle_index],  # Disagree
            category_colors[0:1],             # Strongly Disagree
            category_colors[-1:],             # Strongly Agree
            category_colors[middle_index+1:-1],# Agree
            neutral_color                     # Right half of neutral
        ])
        
        # Reorder labels accordingly
        neutral_label = labels[middle_index]
        reordered_labels = [
            f"{neutral_label} (left)",
            *labels[1:middle_index],          # Disagree
            labels[0],                        # Strongly Disagree
            labels[-1],                       # Strongly Agree
            *labels[middle_index+1:-1],       # Agree
            f"{neutral_label} (right)"
        ]
    else:  # Even number of categories (no neutral)
        # Create the new order: [Disagree, Strongly Disagree | Strongly Agree, Agree]
        reordered_counts = np.column_stack([
            counts[:, 1:middle_index],        # Disagree
            counts[:, 0:1],                   # Strongly Disagree
            counts[:, -1:],                   # Strongly Agree
            counts[:, middle_index:-1]        # Agree
        ])
        
        # Reorder colors accordingly
        reordered_colors = np.vstack([
            category_colors[1:middle_index],  # Disagree
            category_colors[0:1],             # Strongly Disagree
            category_colors[-1:],             # Strongly Agree
            category_colors[middle_index:-1]  # Agree
        ])
        
        # Reorder labels accordingly
        reordered_labels = [
            *labels[1:middle_index],          # Disagree
            labels[0],                        # Strongly Disagree
            labels[-1],                       # Strongly Agree
            *labels[middle_index:-1]          # Agree
        ]
    
    # Calculate positions for each bar segment
    n_segments = reordered_counts.shape[1]
    neg_half = n_segments // 2  # Number of segments on the negative side
    
    # Initialize arrays for start positions
    starts = np.zeros_like(reordered_counts)
    
    # Calculate positions for negative side (right to left from center)
    for i in range(neg_half-1, -1, -1):
        if i == neg_half-1:
            starts[:, i] = -reordered_counts[:, i]  # Start at center
        else:
            starts[:, i] = starts[:, i+1] - reordered_counts[:, i]
    
    # Calculate positions for positive side (left to right from center)
    for i in range(neg_half, n_segments):
        if i == neg_half:
            starts[:, i] = 0  # Start at center
        else:
            starts[:, i] = starts[:, i-1] + reordered_counts[:, i-1]
    
    # Create figure with adjusted dimensions
    adjusted_width = width * zoom_factor
    adjusted_height = height * zoom_factor
    fig, ax = plt.subplots(figsize=(adjusted_width, adjusted_height))
    
    # Set background color to white
    fig.set_facecolor('#FFFFFF')
    
    # Plot each category for each group
    for i, group_name in enumerate(group_names):
        ax.barh(i, reordered_counts[i], left=starts[i], height=0.5, color=reordered_colors)
    
    # Add a dashed vertical line at the center
    ax.axvline(0, linestyle='--', color='grey', alpha=0.5)
    
    # Set x-axis limits and ticks
    max_value = max(abs(starts.min()), abs((starts + reordered_counts).max()))
    max_value = max(max_value, 50)  # Ensure at least -50 to 50 range
    ax.set_xlim(-max_value, max_value)
    ax.set_xticks(np.arange(-max_value, max_value+1, 25))
    ax.xaxis.set_major_formatter(lambda x, pos: str(abs(int(x))))
    
    # Set y-axis
    ax.set_yticks(range(len(group_names)))
    ax.set_yticklabels(group_names)
    
    # Set labels
    ax.set_xlabel(x_label)
    if y_label:
        ax.set_ylabel(y_label)
    
    # Set title
    if title:
        ax.set_title(title)
    
    # Remove spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    # Add legend
    # For legend, use original labels without the (left)/(right) suffix for neutral
    if n_categories % 2 == 1:
        legend_labels = [
            neutral_label,                    # Neutral
            *labels[1:middle_index],          # Disagree
            labels[0],                        # Strongly Disagree
            labels[-1],                       # Strongly Agree
            *labels[middle_index+1:-1]        # Agree
        ]
    else:
        legend_labels = [
            *labels[1:middle_index],          # Disagree
            labels[0],                        # Strongly Disagree
            labels[-1],                       # Strongly Agree
            *labels[middle_index:-1]          # Agree
        ]
    
    legend_items = [mpatches.Patch(color=color, label=label) 
                   for color, label in zip(reordered_colors, legend_labels)]
    ax.legend(handles=legend_items, ncol=len(legend_labels), 
              bbox_to_anchor=(0, -0.1), loc='upper left', fontsize='small')
    
    # Save the plot
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close() 