# AWS Ground Station Integration Guide

## Overview

Ground Station Core now supports **AWS Ground Station** alongside your local ground station hardware. This enables hybrid operations, leveraging Amazon's global network of ground stations for satellite communications.

## Architecture

```
┌────────────────────────────────────────────────────────┐
│                  Ground Station Core                    │
│                                                         │
│  ┌─────────────┐                    ┌──────────────┐  │
│  │   UI Layer  │                    │  API Server  │  │
│  │             │────── Commands ────▶│              │  │
│  │ - Desktop   │                    │  Routing     │  │
│  │ - Web       │◀───── Status ──────│  Logic       │  │
│  └─────────────┘                    └──────┬───────┘  │
│                                             │          │
└─────────────────────────────────────────────┼──────────┘
                                              │
                    ┌─────────────────────────┴──────────┐
                    │                                    │
         ┌──────────▼──────────┐          ┌─────────────▼────────────┐
         │  Local Ground       │          │  AWS Ground Station      │
         │  Station Hardware   │          │                          │
         │                     │          │  - Global network        │
         │  - SDR              │          │  - Managed service       │
         │  - Rotator          │          │  - S3 data storage       │
         │  - Direct control   │          │  - API-based control     │
         └─────────────────────┘          └──────────────────────────┘
```

## Why Use AWS Ground Station?

### Benefits

✅ **Global Coverage**
- 14+ ground stations worldwide
- Better geographic coverage than single site
- Multiple opportunities per orbit

✅ **Managed Infrastructure**
- No hardware maintenance
- Professional-grade equipment
- Automatic failover

✅ **Scalability**
- Pay-per-use pricing
- Schedule multiple satellites
- Burst capacity for campaigns

✅ **Data Pipeline**
- Automatic S3 upload
- CloudWatch monitoring
- Integration with AWS services

### Use Cases

**When to Use AWS:**
- 🌍 Need global coverage
- 📡 Backup for local GS downtime
- 🚀 High-value contacts (critical commands)
- 📊 Large data downlinks
- 🔄 Satellite commissioning phase

**When to Use Local:**
- 🏠 Development and testing
- 💰 Cost-conscious operations
- 🎓 Educational missions
- 🔬 Research experiments
- 🛠️ Custom hardware integration

## Prerequisites

### AWS Account Setup

1. **Create AWS Account**
   - Sign up at https://aws.amazon.com
   - Enable billing

2. **IAM Permissions**
   
   Create IAM user with Ground Station permissions:
   
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "groundstation:*",
           "s3:GetObject",
           "s3:PutObject",
           "s3:ListBucket",
           "ec2:DescribeAddresses",
           "ec2:DescribeNetworkInterfaces"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

3. **Configure AWS CLI**
   ```powershell
   pip install awscli
   aws configure
   ```
   
   Enter:
   - AWS Access Key ID
   - AWS Secret Access Key
   - Default region (e.g., us-west-2)
   - Output format: json

### Ground Station Core Setup

1. **Install boto3**
   ```powershell
   pip install boto3 botocore
   ```

2. **Verify Installation**
   ```python
   import boto3
   client = boto3.client('groundstation', region_name='us-west-2')
   print(client.list_ground_stations())
   ```

## Configuration

### In Desktop UI (ui_v2.py)

1. **Open Settings Tab** (⚙️)

2. **Ground Station Selection Section:**
   - Select: ☁️ AWS Ground Station

3. **AWS Configuration Panel** (appears when AWS selected):
   - **AWS Region**: Enter your region (e.g., `us-west-2`)
   - **Ground Station ID**: Your AWS GS ID (e.g., `gs-1234`)
   - **Mission Profile ARN**: Full ARN of your mission profile
   
   Example:
   ```
   arn:aws:groundstation:us-west-2:123456789012:mission-profile/1234abcd-56ef-78gh-90ij-klmnopqrstuv
   ```

4. **Test Connection:**
   - Click "Test AWS Connection"
   - Should show: "✓ Successfully connected..."

### In Web UI (streamlit_ui.py)

1. **Sidebar → Configuration**

2. **Ground Station Radio Button:**
   - Select: ☁️ AWS Ground Station

3. **AWS Configuration Expander:**
   - AWS Region: `us-west-2`
   - Ground Station ID: `your-gs-id`
   - Mission Profile ARN: `arn:aws:...`

4. **Test Connection:**
   - Click "Test AWS Connection"
   - Success message appears

### Programmatic Configuration

Using `aws_integration.py`:

```python
from aws_integration import AWSGroundStationConfig, AWSGroundStationManager

# Create configuration
config = AWSGroundStationConfig(
    region="us-west-2",
    ground_station_id="gs-1234abcd",
    mission_profile_arn="arn:aws:groundstation:us-west-2:123456789012:mission-profile/5678efgh",
    satellite_arn="arn:aws:groundstation::123456789012:satellite/9012ijkl"
)

# Create manager
manager = AWSGroundStationManager(config)

# Test connection
stations = manager.client.list_ground_stations()
print(f"Available stations: {len(stations)}")
```

## AWS Ground Station Setup

### 1. Register Your Satellite

In AWS Console:

1. Navigate to **AWS Ground Station**
2. **Satellites** → **Add satellite**
3. Enter:
   - Satellite name
   - NORAD ID
   - TLE data
4. Save

### 2. Create Mission Profile

A mission profile defines your communication parameters:

1. **Mission Profiles** → **Create mission profile**
2. Configure:
   - **Name**: e.g., "My-Satellite-Downlink"
   - **Minimum elevation**: 10°
   - **Contact pre-pass duration**: 5 minutes
   - **Contact post-pass duration**: 5 minutes

3. **Dataflow endpoints**:
   - Create S3 dataflow endpoint
   - Specify S3 bucket for data delivery

4. **Tracking configuration**:
   - Enable autotracking
   - Set tracking rate

5. Save and note the **ARN**

### 3. Create Dataflow Endpoint Group

For data delivery:

1. **Dataflow endpoints** → **Create endpoint group**
2. Choose:
   - **S3 Recording**: For storing downlink data
   - Configure bucket and path
3. Link to mission profile

### 4. Schedule Contacts

Manually or programmatically reserve satellite passes.

## Usage Examples

### Example 1: Find Available Passes

```python
from aws_integration import AWSGroundStationManager, AWSGroundStationConfig

config = AWSGroundStationConfig(
    region="us-west-2",
    ground_station_id="gs-1234",
    mission_profile_arn="arn:aws:groundstation:...:mission-profile/5678"
)

manager = AWSGroundStationManager(config)

# Find passes in next 24 hours
passes = manager.find_available_passes(
    satellite_arn="arn:aws:groundstation::123456789012:satellite/9012",
    duration_hours=24,
    min_elevation=10.0
)

for p in passes:
    print(f"AOS: {p.start_time}, Max El: {p.maximum_elevation}°")
```

### Example 2: Schedule a Pass

```python
from datetime import datetime, timedelta

# Schedule pass starting in 2 hours
start_time = datetime.utcnow() + timedelta(hours=2)
end_time = start_time + timedelta(minutes=10)

contact_id = manager.schedule_pass(
    satellite_arn="arn:aws:groundstation::123456789012:satellite/9012",
    start_time=start_time,
    end_time=end_time,
    tags={"mission": "test", "operator": "john"}
)

print(f"Scheduled contact: {contact_id}")
```

### Example 3: Monitor Pass Execution

```python
contact_id = "c-1234567890abcdef"

status = manager.get_pass_status(contact_id)
print(f"Status: {status['contactStatus']}")
print(f"Ground Station: {status['groundStation']}")
print(f"Start: {status['startTime']}")
print(f"End: {status['endTime']}")
```

### Example 4: Download Contact Data

```python
# After contact completes, download data from S3
manager.client.download_contact_data(
    contact_id="c-1234567890abcdef",
    s3_bucket="my-satellite-data",
    local_path="./downloads/"
)
```

### Example 5: Cancel Scheduled Pass

```python
contact_id = "c-1234567890abcdef"
success = manager.cancel_pass(contact_id)

if success:
    print("Pass cancelled successfully")
```

## Command Routing

When AWS Ground Station is selected, commands are routed through AWS APIs:

### Local Ground Station Flow
```
UI → API Server → uplink.py → SDR → Satellite
```

### AWS Ground Station Flow
```
UI → API Server → aws_integration.py → AWS API → AWS GS → Satellite
```

The backend API server (`backend/api_server.py`) automatically handles routing based on the selected ground station type.

## Cost Optimization

### AWS Ground Station Pricing (as of 2024)

- **Antenna time**: ~$3-10 per minute (varies by region/frequency)
- **Data transfer**: Standard AWS data transfer rates
- **S3 storage**: Standard S3 pricing

### Tips to Reduce Costs

1. **Optimize Pass Selection**
   - Schedule only high-elevation passes (>30°)
   - Prioritize critical contacts

2. **Use Local GS for Testing**
   - Develop and test locally
   - Use AWS only for production

3. **Efficient Scheduling**
   - Batch commands in fewer contacts
   - Cancel unused reservations 24+ hours ahead

4. **Data Management**
   - Enable S3 lifecycle policies
   - Archive to Glacier after 30 days

5. **Regional Selection**
   - Choose closest AWS region
   - Reduces data transfer costs

## Integration with Ground Station Core

### Switching Between Local and AWS

**Runtime Switching:**
- Both UIs support real-time switching
- No restart required
- State preserved

**Command Sending:**
```python
# UI automatically routes based on selection
if ground_station_type == "aws":
    # Use AWS Ground Station API
    aws_manager.schedule_pass(...)
else:
    # Use local SDR
    uplink.send_command(...)
```

### Hybrid Operations

Run both simultaneously:
- **Local**: Real-time development and testing
- **AWS**: Critical operations and data downlinks

### Data Synchronization

Commands sent via AWS are logged in the same system:
- Activity log shows source (Local/AWS)
- Telemetry tagged with ground station
- Pass schedules unified view

## Monitoring and Logging

### CloudWatch Integration

AWS Ground Station logs to CloudWatch:

```python
import boto3

logs = boto3.client('logs', region_name='us-west-2')

# Get contact logs
response = logs.filter_log_events(
    logGroupName='/aws/groundstation/contacts',
    filterPattern=f'contactId = {contact_id}'
)

for event in response['events']:
    print(event['message'])
```

### Local Logging

Ground Station Core logs AWS operations:

```
[2025-10-28 14:32:15] 🌐 Switched to AWS Ground Station
[2025-10-28 14:35:20] ✓ Connected to AWS Ground Station: us-west-2
[2025-10-28 14:40:15] Scheduled AWS contact: c-abc123def456
[2025-10-28 15:30:00] AWS contact started: c-abc123def456
[2025-10-28 15:40:00] AWS contact completed: c-abc123def456
```

## Troubleshooting

### Issue: "Import 'boto3' could not be resolved"

**Solution:**
```powershell
pip install boto3
```

### Issue: "Access Denied" errors

**Solution:**
- Verify IAM permissions
- Check AWS credentials: `aws configure list`
- Test with: `aws groundstation list-ground-stations`

### Issue: "No ground stations available"

**Solution:**
- Check selected region has AWS GS
- Verify satellite is registered in AWS
- Ensure mission profile is created

### Issue: "Mission profile ARN invalid"

**Solution:**
- Copy full ARN from AWS Console
- Format: `arn:aws:groundstation:region:account:mission-profile/id`
- Check region matches

### Issue: Contact scheduling fails

**Solution:**
- Verify satellite is visible from GS
- Check time is in future
- Ensure no overlapping contacts
- Verify mission profile is active

## Security Best Practices

1. **IAM Roles**
   - Use IAM roles, not root credentials
   - Follow least privilege principle
   - Rotate keys regularly

2. **S3 Bucket Security**
   - Enable encryption at rest
   - Use bucket policies
   - Enable versioning

3. **Network Security**
   - Use VPC endpoints where possible
   - Enable CloudTrail logging
   - Monitor API calls

4. **Access Control**
   - Implement MFA for AWS Console
   - Use separate accounts for dev/prod
   - Audit permissions regularly

## Advanced Features

### Multi-Region Support

```python
# Deploy across multiple regions
regions = ["us-west-2", "eu-north-1", "ap-southeast-2"]

managers = {}
for region in regions:
    config = AWSGroundStationConfig(
        region=region,
        ground_station_id=f"gs-{region}",
        mission_profile_arn=f"arn:aws:groundstation:{region}:..."
    )
    managers[region] = AWSGroundStationManager(config)

# Find best pass across all regions
all_passes = []
for region, manager in managers.items():
    passes = manager.find_available_passes(satellite_arn, 24, 10.0)
    all_passes.extend([(region, p) for p in passes])

# Sort by elevation
best_pass = max(all_passes, key=lambda x: x[1].maximum_elevation)
print(f"Best pass: {best_pass[0]} at {best_pass[1].start_time}")
```

### Automated Scheduling

```python
import schedule
import time

def auto_schedule_passes():
    """Automatically schedule high-elevation passes"""
    passes = manager.find_available_passes(satellite_arn, 24, 30.0)
    
    for p in passes:
        if p.maximum_elevation > 45:  # Only schedule good passes
            contact_id = manager.schedule_pass(
                satellite_arn=satellite_arn,
                start_time=p.start_time,
                end_time=p.end_time,
                tags={"auto": "true"}
            )
            print(f"Auto-scheduled: {contact_id}")

# Run every 6 hours
schedule.every(6).hours.do(auto_schedule_passes)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## References

- **AWS Ground Station Docs**: https://docs.aws.amazon.com/ground-station/
- **Boto3 Documentation**: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/groundstation.html
- **Pricing Calculator**: https://calculator.aws/#/addService/GroundStation
- **Getting Started Guide**: https://aws.amazon.com/ground-station/getting-started/

## Support

For issues:
1. Check CloudWatch logs
2. Review IAM permissions
3. Verify mission profile configuration
4. Test with AWS CLI first
5. Check Ground Station Core logs

For AWS-specific issues, contact AWS Support or consult AWS documentation.
