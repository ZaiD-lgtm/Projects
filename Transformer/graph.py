import pandas as pd
import matplotlib.pyplot as plt

# Load your CSV file
# CSV format: Row,Windowed loss,Cumulative Loss
df = pd.read_csv("loss_report.csv")

# Drop duplicate 'Row' entries — keeping first occurrence
row_counts = df['Row'].value_counts()
rows_appearing_twice = row_counts[row_counts == 2].index
df_to_process = df[df['Row'].isin(rows_appearing_twice)]
df_processed_sorted = df_to_process.sort_values(by=['Row', 'Windowed loss'])
df_rows_to_keep_from_duplicates = df_processed_sorted.drop_duplicates(subset=['Row'], keep='first')
df_single_occurrence_rows = df[~df['Row'].isin(rows_appearing_twice)]
final_df = pd.concat([df_single_occurrence_rows, df_rows_to_keep_from_duplicates])
final_df = final_df.sort_values(by='Row').reset_index(drop=True)

# Save cleaned CSV back
csv_filename = 'loss_report.csv'
final_df.to_csv(csv_filename, index=False)
print(f"DataFrame successfully saved to '{csv_filename}', overwriting any existing content.")

# Reload cleaned data
df = pd.read_csv("loss_report.csv")


df = df[df['Windowed loss'] <= 6].reset_index(drop=True)
# Compute Moving Averages (adjust window size as needed)
window_size = 10
df['Windowed_MA'] = df['Windowed loss'].rolling(window=window_size, center=True).mean()
df['Cumulative_MA'] = df['Cumulative Loss'].rolling(window=window_size, center=True).mean()

# Plotting
plt.figure(figsize=(14, 7))

# Plot windowed loss
plt.plot(df['Row'], df['Windowed loss'], label="800-Sample Window Loss",
         color='dodgerblue', linewidth=1.8, alpha=0.7)

# Plot moving average of windowed loss
plt.plot(df['Row'], df['Windowed_MA'], label=f"Moving Avg ({window_size}-point)", 
         color='purple', linewidth=2.2)

# Plot cumulative loss
plt.plot(df['Row'], df['Cumulative Loss'], label="Cumulative Loss",
         color='orange', linewidth=2, linestyle='--', alpha=0.8)

# Plot moving average of cumulative loss
plt.plot(df['Row'], df['Cumulative_MA'], label=f"Cumulative Moving Avg ({window_size}-point)",
         color='green', linewidth=2, linestyle='-.')

# Highlight minimum point on windowed loss
min_win_idx = df['Windowed loss'].idxmin()
plt.scatter(df['Row'][min_win_idx], df['Windowed loss'][min_win_idx],
            color='red', s=70, zorder=5, label=f"Min Window Loss: {df['Windowed loss'][min_win_idx]:.4f}")

# Highlight minimum point on cumulative loss
min_cum_idx = df['Cumulative Loss'].idxmin()
plt.scatter(df['Row'][min_cum_idx], df['Cumulative Loss'][min_cum_idx],
            color='green', s=70, zorder=5, label=f"Min Cumulative Loss: {df['Cumulative Loss'][min_cum_idx]:.4f}")

# Labels, title, legend, and grid
plt.title("Training Loss Curves with Moving Averages", fontsize=18)
plt.xlabel("Training Rows", fontsize=14)
plt.ylabel("Loss", fontsize=14)
plt.legend(fontsize=12)
plt.grid(True, linestyle='--', alpha=0.4)

plt.tight_layout()
plt.show()

