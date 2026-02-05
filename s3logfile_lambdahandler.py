import boto3
import re
from collections import Counter

s3 = boto3.client('s3')

def lambda_handler(event, context):
    # Configuration
    source_bucket = "ec2bucket-dummy"
    target_bucket = "amzn-s3-destination-bucket-1"
    report_file_name = "error_report.txt"
    
    # 1. List objects in the source bucket
    response = s3.list_objects_v2(Bucket=source_bucket)
    
    if 'Contents' not in response:
        print("No files found in source bucket.")
        return {"message": "No files found in source bucket."}
    
    error_counter = Counter()
    processed_files = 0
    
    # 2. Process the files
    for obj in response['Contents'][:20]:
        file_key = obj['Key']
        
        try:
            # Download file content
            log_obj = s3.get_object(Bucket=source_bucket, Key=file_key)
            log_content = log_obj['Body'].read().decode('utf-8')
            
            # 3. Flexible Regex: 
            found_errors = re.findall(r'(?:\[?ERROR\]?)[: \s]*(.*)', log_content, re.IGNORECASE)
            
            # Update the global counter
            error_counter.update(found_errors)
            processed_files += 1
            
            print(f"Processed {file_key}: Found {len(found_errors)} errors.")
            
        except Exception as e:
            print(f"Error processing file {file_key}: {e}")

    # 4. Generate the report content
    report_lines = [
        f"ERROR ANALYSIS REPORT\n",
        f"Date: {context.aws_request_id}\n", # Using request ID as a unique ref
        f"Files Processed: {processed_files}\n",
        "="*40 + "\n",
        "{:<10} | {}\n".format("COUNT", "ERROR MESSAGE"),
        "-"*40 + "\n"
    ]
    
    # Add sorted error counts to the report
    for error, count in error_counter.most_common():
        report_lines.append("{:<10} | {}\n".format(count, error))
    
    report_body = "".join(report_lines)

    # 5. Upload the final report
    s3.put_object(
        Bucket=target_bucket,
        Key=report_file_name,
        Body=report_body,
        ContentType='text/plain'
    )

    return {
        "statusCode": 200,
        "body": f"Processed {processed_files} files. Created {report_file_name} in {target_bucket}."
    }