import json
import getpass
import argparse
import requests
import csv

def json_to_markdown(data):
    markdown = ""
    
    # Assuming the JSON data is a dictionary
    if isinstance(data, dict):
        for key, value in data.items():
            markdown += f"## {key}\n"
            markdown += json_to_markdown(value)
            markdown += "\n"
    
    # Assuming the JSON data is a list
    elif isinstance(data, list):
        for item in data:
            markdown += json_to_markdown(item)
            markdown += "\n"
    
    # Assuming the JSON data is a scalar value
    else:
        markdown += str(data)
    
    return markdown

def main(client_id, secret_key, output_file, output_format):
    # login
    jwt = login(client_id, secret_key)

    # Get All Policies
    policies = get_policies(jwt)

    # Sort policies alphabetically based on 'displayName'
    policies.sort(key=lambda x: x['displayName'])

    # Generate output based on format
    if output_format == 'markdown':
        markdown_content = generate_markdown(policies)
        write_output(markdown_content, output_file)
    elif output_format == 'csv':
        csv_content = generate_csv(policies)
        write_output(csv_content, output_file)
    else:
        print("Invalid output format. Supported formats are 'markdown' and 'csv'.")


def generate_csv(policies):
    csv_content = []
    csv_content.append(['UID', 'Display Name', 'Risk Type', 'Severity', 'Policy Groups', 'Active Issues', 'Created By', 'IsEnabled', 'Description'])
    for policy in policies:
        policy_groups = ", ".join([group['name'] for group in policy['policyGroups']])
        csv_content.append([policy['uid'], policy['displayName'], policy['riskType'], policy['severity'], policy_groups, policy['activeIssuesCount'], policy['createdBy'], policy['isEnabled'], policy['description']])
        # csv_content.append([policy['uid'], policy['displayName'], policy['riskType'], policy['severity'], policy_groups, "description"])
    
    return csv_content

def write_output(content, output_file):
    if output_file:
        with open(output_file, "w") as f:
            if isinstance(content, str):
                f.write(content)
            elif isinstance(content, list):
                writer = csv.writer(f)
                writer.writerows(content)
    else:
        print(content)



def generate_markdown(policies):
    markdown = "# Policies\n"
    for policy in policies:
        markdown += f"## {policy['displayName']}\n"
        markdown += "### Risk Type:\n"
        markdown += f"**{policy['riskType']}**\n"
        markdown += "### Severity:\n"
        markdown += f"**{policy['severity']}**\n"
        markdown += "### Policy Groups\n"
        for policy_group in policy['policyGroups']:
            markdown += f"* {policy_group['name']}\n"
        markdown += "### **Description**\n"
        markdown += f"{policy['description']}\n\n"

    return markdown

def login(client_id, secret_key):
    #login url
    url = "https://api.cyera.io/v1/login"
    
    # payload
    payload = json.dumps({
        "clientId": f"{client_id}",
        "secret": f"{secret_key}"
    })

    # headers
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.json().get("jwt")

def get_policies(jwt):
    url = "https://app.cyera.io/api/policies/allPolicies"
    all_policies = []
    page = 1

    # headers
    headers = {
        'Authorization': f'Bearer {jwt}', 
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    
    while True:
        response = requests.get(url, params={"page": page, "limit": "10"}, headers=headers)
        data = response.json()
        policies = data.get("policies", [])
        all_policies.extend(policies)
        
        total_pages = data["meta"]["totalPages"]
        if page >= total_pages:
            break
        
        page += 1
    
    return all_policies


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export Cyera Policies")
    parser.add_argument('-c', '--client_id', type=str, required=True, help="The client ID from API Key created in UI settings")
    parser.add_argument('-o', '--output', type=str, help="Output file to save content")
    parser.add_argument('-f', '--format', choices=['markdown', 'csv'], default='markdown', help="Output format (default: markdown)")
    args = parser.parse_args()
    
    # Prompt for password securely
    secret_key = getpass.getpass(prompt="Enter your secret_key: ")

    main(args.client_id, secret_key, args.output, args.format)
