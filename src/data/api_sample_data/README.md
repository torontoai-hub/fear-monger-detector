Key Differences at a Glance:
1. Data Structure

Fitbit: Simple flat array, time-only timestamps (REST API)
Apple HealthKit: Rich objects with extensive metadata, device info, motion context
Android Health Connect: Flexible records with multiple samples, origin tracking

2. Timestamp Formats

Fitbit: "10:31:15" (time only + date param)
Apple: "2025-09-29T10:31:15.000-0400" (with timezone)
Android: "2025-09-29T10:31:15.000Z" (UTC)

3. Heart Rate Values

Fitbit: Integer value: 125
Apple: Double with unit quantity: { unit: "count/min", value: 125.0 }
Android: Long beatsPerMinute: 125

4. Unique Features

Fitbit: Heart rate zones, resting HR, calorie burn
Apple: Motion context (0=sedentary, 1=active), background delivery
Android: Multi-app data aggregation, flexible sample grouping