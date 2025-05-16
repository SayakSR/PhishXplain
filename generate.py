import json
import os
import ollama
import re

def load_json(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_feature_dict(txt_path):
    with open(txt_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_summary_prompt(elements_json, feature_dict):
    feature_list_text = ", ".join(feature_dict.keys())
    prompt = f"""
You are presented with a structured list that collectively represents a single phishing webpage.

Each entry includes:
- Text content
- Screen coordinates (approximate location on the page)
- HTML element type(s) (e.g., button, input, p, span, etc.)

Your task is:
- Look at the entire webpage holistically.
- Analyze whether this webpage shows signs of phishing or malicious behavior.
- Summarize **why** the website is phishing — citing specific elements (by the element number) as evidence.
- Where appropriate, tie your observations back to known phishing features such as: {feature_list_text}.
- Be conservative: only highlight evidence that clearly suggests phishing intent.

Return your output as a **natural language paragraph** (not a JSON object, no lists).

Here is the structured representation of the webpage:

{json.dumps(elements_json, indent=2)}
"""
    return prompt

def build_elementwise_prompt(summary_text, feature_dict):
    feature_list_text = ", ".join(feature_dict.keys())
    prompt = f"""
You have the following phishing website summary:

\"\"\"{summary_text}\"\"\"

Your task now is:
- For each ELEMENT_x mentioned in the summary, output a mapping:
    element_x: {{feature_name, one or two sentences explaining why}}
- **IMPORTANT:** The feature_name must be **strictly chosen from the following list**: {feature_list_text}.
- The explanation should point out specific problematic artifacts.
- **DO NOT** mention any element numbers in your explanations.
- Only output in this exact format:
    element_x: {{feature_name, one or two sentences why}}
    element_y: {{feature_name, one or two sentences why}}
    (and so on...)
- Do not add any extra text, no preambles, no comments, no explanations. Only the mapping output.

Start now:
"""
    return prompt


def ask_llama(prompt):
    response = ollama.chat(model="llama3.2:3b", messages=[
        {"role": "user", "content": prompt}
    ])
    return response['message']['content']

def save_output(content, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Saved output to {output_path}")

def generate_warning(elementwise_mapping, feature_dict):
    print("\n🔍 Debugging elementwise mapping parsing:")
    print("Raw mapping:", elementwise_mapping)
    
    # Parse the elementwise mapping to extract features and their priorities
    feature_priority_map = {}
    element_explanations = {}
    
    # Split the mapping into lines and process each line
    lines = elementwise_mapping.strip().split('\n')
    for line in lines:
        if ':' in line:
            # Split on the first colon to separate element number from content
            element_part, content = line.split(':', 1)
            element_num = element_part.strip()
            # Split the content on the first comma to separate feature name from explanation
            parts = content.strip().split(',', 1)
            if len(parts) >= 1:
                feature_name = parts[0].strip()
                explanation = parts[1].strip() if len(parts) > 1 else ''
                print(f"\nProcessing feature: '{feature_name}'")
                
                # Find the priority for this feature
                for name, priority in feature_dict.items():
                    if name == feature_name:
                        print(f"Found priority: {priority} for feature: {name}")
                        feature_priority_map[priority] = {
                            'name': name,
                            'explanation': explanation,
                            'element': element_num
                        }
                        break
    
    print("\nFeature priority map:", feature_priority_map)
    
    # Sort by priority (P1, P2, P3, etc.)
    sorted_features = sorted(feature_priority_map.items(), key=lambda x: int(x[0][1:]))
    print("\nSorted features:", sorted_features)
    
    # Take top 3 highest priority features
    top_features = sorted_features[:3]
    print("\nTop 3 features:", top_features)
    
    # Create dictionary of highest priority elements and their explanations
    highest_priority_dict = {}
    for priority, feature in top_features:
        highest_priority_dict[feature['element']] = {
            'feature_name': feature['name'],
            'explanation': feature['explanation']
        }
    
    # Generate warning message
    warning = "⚠️ HIGHEST PRIORITY PHISHING INDICATORS:\n\n"
    for priority, feature in top_features:
        warning += f"🔴 {priority} - {feature['name']}\n"
        warning += f"   {feature['explanation']}\n\n"
    
    # Save the dictionary to a separate file
    with open(os.path.join(artifacts_dir, "highest_priority_elements.json"), 'w', encoding='utf-8') as f:
        json.dump(highest_priority_dict, f, indent=4)
    print(f"✅ Saved highest priority elements to artifacts/highest_priority_elements.json")
    
    return warning

if __name__ == "__main__":
    # Create artifacts directory if it doesn't exist
    artifacts_dir = "artifacts"
    os.makedirs(artifacts_dir, exist_ok=True)

    json_path = os.path.join(artifacts_dir, "website_text_coordinates.json")
    feature_list_path = "feature_list.txt"
    summary_output_path = os.path.join(artifacts_dir, "website_phishing_summary.txt")
    elementwise_output_path = os.path.join(artifacts_dir, "website_elementwise_mapping.txt")
    warning_output_path = os.path.join(artifacts_dir, "website_warning.txt")

    print("🔍 Loading website elements...")
    elements_json = load_json(json_path)

    print("🔍 Loading feature dictionary...")
    feature_dict = load_feature_dict(feature_list_path)

    print("📝 Building LLaMA summary prompt...")
    summary_prompt = build_summary_prompt(elements_json, feature_dict)

    print("🚀 Generating phishing summary...")
    phishing_summary = ask_llama(summary_prompt)

    print("\n✅ Summary of website phishing indicators:\n")
    print(phishing_summary)
    save_output(phishing_summary, summary_output_path)

    print("\n📝 Building elementwise mapping prompt...")
    elementwise_prompt = build_elementwise_prompt(phishing_summary, feature_dict)

    print("🚀 Generating elementwise feature mapping...")
    elementwise_mapping = ask_llama(elementwise_prompt)

    print("\n✅ Elementwise phishing indicators:\n")
    print(elementwise_mapping)
    save_output(elementwise_mapping, elementwise_output_path)

    print("\n🚨 Generating warning based on highest priority features...")
    warning = generate_warning(elementwise_mapping, feature_dict)
    print("\n" + warning)
    save_output(warning, warning_output_path)

    print("\n🏁 All done!")

