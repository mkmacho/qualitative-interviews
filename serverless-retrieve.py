from boto3 import resource
from argparse import ArgumentParser
from csv import DictWriter

def retrieve_all_sessions(table_name:str, output_path:str, print_chats:bool=False):
    """ 
    Retrieve chat history (as long, session-message stored data) to CSV 
    (and optionally `print_chats`) for all sessions from `table_name` table.
    Will save CSV to the required `output_path` filepath.
    """
    # Retrieve interview sessions from DynamoDB
    table = resource('dynamodb').Table(table_name)
    all_interview_chats = []
    last_eval = None
    while True:
        # Handle multiple chunks with contiguous scan
        resp = table.scan(ExclusiveStartKey=last_eval) if last_eval else table.scan()
        for item in resp.get('Items', []):
            session_messages = item['session']
            # Add all messages in current interview session
            all_interview_chats.extend(session_messages)
            if print_chats: # Print each session-message to console
                for message in session_messages:
                    print(message)
        if not resp.get('LastEvaluatedKey'): break
        last_eval = resp['LastEvaluatedKey']

    print(f"{len(all_interview_chats)} interview sessions retrieved!")
    if not all_interview_chats: return

    # Save to specified CSV output filepath
    with open(output_path, 'w') as csvfile:
        writer = DictWriter(csvfile, fieldnames=all_interview_chats[0].keys())
        writer.writeheader()
        writer.writerows(all_interview_chats)
    

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('--table_name', type=str, help="Name of DynamoDBTable")
    parser.add_argument('--output_path', type=str, default="chats.csv", help="Filepath to chats CSV")
    args = parser.parse_args()
    retrieve_all_sessions(args.table_name, args.output_path)
    