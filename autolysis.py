import os
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import requests

aiproxy_token = os.getenv("eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIyZjMwMDE2NTJAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.6Awo3wRrJsUNnYb5ExJuXDn0QfrsZ7uhTCjp6ILYsyA")

def load_data(file_path):
    """Load data from a CSV file."""
    try:
        return pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        return pd.read_csv(file_path, encoding='latin1')

def basic_analysis(df):
    """Perform basic analysis on the dataset."""
    analysis = {}
    analysis['shape'] = df.shape
    analysis['columns'] = df.columns.tolist()
    analysis['dtypes'] = df.dtypes.apply(lambda x: str(x)).tolist()
    analysis['summary'] = df.describe(include='all').to_dict()
    analysis['missing_values'] = df.isnull().sum().to_dict()
    return analysis

def generate_plots(df):
    """Generate basic visualizations and save them as PNG files."""
    sns.set(style="darkgrid")
    image_files = []

    # Distribution plot for numerical columns
    numeric_cols = df.select_dtypes(include='number').columns
    for col in numeric_cols:
        plt.figure(figsize=(10, 6))
        sns.histplot(df[col], kde=True)
        plt.title(f'Distribution of {col}')
        image_file = f'{col}_distribution.png'
        plt.savefig(image_file)
        image_files.append(image_file)
        plt.close()

    # Pairplot for numerical columns
    if len(numeric_cols) > 1:
        sns.pairplot(df[numeric_cols])
        image_file = 'pairplot.png'
        plt.savefig(image_file)
        image_files.append(image_file)
        plt.close()

    # Heatmap for correlation matrix
    if len(numeric_cols) > 1:
        corr = df[numeric_cols].corr()
        plt.figure(figsize=(12, 8))
        sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f')
        plt.title('Correlation Matrix')
        image_file = 'correlation_matrix.png'
        plt.savefig(image_file)
        image_files.append(image_file)
        plt.close()

    return image_files

def query_llm(prompt):
    """Query the LLM with a given prompt."""
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

def create_readme(analysis, story, image_files):
    """Create a README.md file with the analysis story."""
    with open("README.md", "w") as f:
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

def main(file_path):
    df = load_data(file_path)
    analysis = basic_analysis(df)
    
    image_files = generate_plots(df)
    
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
    
    create_readme(analysis, story, image_files)

if __name__ == "__main__":
    file_path = 'd:/goodreads.csv'
    main(file_path)
