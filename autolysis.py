import os
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import requests

# Function to load data from a CSV file
def load_data(file_path):
    """Load data from a CSV file."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    try:
        return pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        return pd.read_csv(file_path, encoding='latin1')

# Function for basic analysis on the dataset
def basic_analysis(df):
    """Perform basic analysis on the dataset."""
    analysis = {}
    analysis['shape'] = df.shape
    analysis['columns'] = df.columns.tolist()
    analysis['dtypes'] = df.dtypes.apply(lambda x: str(x)).tolist()
    analysis['summary'] = df.describe(include='all').to_dict()
    analysis['missing_values'] = df.isnull().sum().to_dict()
    return analysis

# Function to generate visualizations and save them as PNG files
def generate_plots(df, output_dir):
    """Generate basic visualizations and save them as PNG files."""
    sns.set(style="darkgrid")
    image_files = []
    image_limit = 3  # Maximum number of images to generate
    image_count = 0

    # Distribution plot for numerical columns
    numeric_cols = df.select_dtypes(include='number').columns
    for col in numeric_cols:
        if image_count >= image_limit:
            break
        plt.figure(figsize=(10, 6))
        sns.histplot(df[col], kde=True)
        plt.title(f'Distribution of {col}')
        image_file = os.path.join(output_dir, f'{col}_distribution.png')
        plt.savefig(image_file)
        image_files.append(image_file)
        plt.close()
        image_count += 1

    # Pairplot for numerical columns
    if image_count < image_limit and len(numeric_cols) > 1:
        sns.pairplot(df[numeric_cols])
        image_file = os.path.join(output_dir, 'pairplot.png')
        plt.savefig(image_file)
        image_files.append(image_file)
        plt.close()
        image_count += 1

    # Heatmap for correlation matrix
    if image_count < image_limit and len(numeric_cols) > 1:
        corr = df[numeric_cols].corr()
        plt.figure(figsize=(12, 8))
        sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f')
        plt.title('Correlation Matrix')
        image_file = os.path.join(output_dir, 'correlation_matrix.png')
        plt.savefig(image_file)
        image_files.append(image_file)
        plt.close()
        image_count += 1

    return image_files

# Function to query the LLM for insights
def query_llm(prompt):
    """Query the LLM with a given prompt."""
    aiproxy_token = os.getenv("eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIyZjMwMDE2NTJAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.6Awo3wRrJsUNnYb5ExJuXDn0QfrsZ7uhTCjp6ILYsyA")
    if not aiproxy_token:
        raise EnvironmentError("AIPROXY_TOKEN not found in environment variables.")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {aiproxy_token}"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(
        "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions",
        headers=headers,
        json=data
    )
    
    if response.status_code != 200:
        raise Exception(f"Error querying LLM: {response.status_code} {response.text}")
    
    response_json = response.json()
    if 'choices' not in response_json:
        raise KeyError(f"Unexpected response format: {response_json}")
    
    return response_json['choices'][0]['message']['content'].strip()

# Function to create the README.md with analysis story and images
def create_readme(analysis, story, image_files, output_dir):
    """Create a README.md file with the analysis story."""
    readme_path = os.path.join(output_dir, "README.md")
    with open(readme_path, "w") as f:
        f.write("# Automated Data Analysis Report\n\n")
        f.write("## Analysis Summary\n\n")
        f.write("### Dataset Overview\n")
        f.write(f"Number of rows: {analysis['shape'][0]}\n")
        f.write(f"Number of columns: {analysis['shape'][1]}\n\n")
        f.write("### Column Information\n")
        for col, dtype in zip(analysis['columns'], analysis['dtypes']):
            f.write(f"- {col} ({dtype})\n")
        f.write("\n### Missing Values\n")
        for col, missing in analysis['missing_values'].items():
            f.write(f"- {col}: {missing} missing values\n")
        f.write("\n### Summary Statistics\n")
        for col, stats in analysis['summary'].items():
            f.write(f"#### {col}\n")
            for stat, value in stats.items():
                f.write(f"- {stat}: {value}\n")
            f.write("\n")
        f.write("## Analysis Story\n\n")
        f.write(story)
        f.write("\n## Visualizations\n\n")
        for img in image_files:
            f.write(f"![{img}](./{img})\n")

# Main function to run the analysis
def main():
    # Check if the file path is provided via command-line argument
    if len(sys.argv) != 2:
        print("Usage: python autolysis.py <path_to_csv_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    
    # Check if the file exists
    if not os.path.isfile(file_path):
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)

    # Create output directory based on the file name
    output_dir = os.path.splitext(os.path.basename(file_path))[0]
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Load and analyze the dataset
    df = load_data(file_path)
    analysis = basic_analysis(df)
    
    # Generate visualizations
    image_files = generate_plots(df, output_dir)
    
    # Query the LLM for analysis insights
    prompt = (
        "Analyze the following dataset summary and provide insights:\n\n"
        f"Columns: {', '.join(analysis['columns'])}\n"
        f"Data types: {', '.join(analysis['dtypes'])}\n"
        f"Summary statistics: {analysis['summary']}\n"
        f"Missing values: {analysis['missing_values']}\n"
    )
    try:
        story = query_llm(prompt)
    except Exception as e:
        story = f"Failed to query LLM: {e}"
    
    # Create README file with the analysis and visualizations
    create_readme(analysis, story, image_files, output_dir)

# Entry point for the script
if __name__ == "__main__":
    main()
