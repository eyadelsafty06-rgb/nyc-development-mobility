# NYC Development and School-Bus Disruption

Data Engineering and Visualization — GIU, Winter 2026

## About the project

This project explores whether development activity and reported school-bus
disruption follow similar patterns across New York City's five boroughs.

We use two NYC Open Data datasets: approved building permits and school-bus
breakdown/delay reports. We clean them separately, summarize them by borough
and month, and combine those summaries for analysis.

The analysis covers January 2022 to December 2024.

Our main question is:

Do changes in development activity coincide with changes in reported
school-bus disruption?

This is an exploratory analysis. A relationship between the two measures
does not prove that development activity causes bus delays.

## Team

Replace the placeholders with the team's names and student IDs.
The responsibilities below are the planned division of work. Update them
to reflect what each person actually completed.

| Member | Name and student ID | Questions | Responsibilities |
|---|---|---|---|
| 1 | [Eyad ELsafty, 16003613] | Q1 and Q2 | Housing cleaning and EDA; borough and year controls |
| 2 | [Name, ID] | Q3 and Q4 | Transportation cleaning and EDA; category controls |
| 3 | [Name, ID] | Q5 and Q6 | Aggregation and integration; report generation |
| 4 | [Name, ID] | Q7 and Q8 | Validation; search, Story section, and deployment |

## Datasets

### 1. DOB NOW: Build – Approved Permits

Domain: Housing and Development

Dataset ID: `rbx6-tga4`

- Dataset page: https://data.cityofnewyork.us/d/rbx6-tga4
- API: https://data.cityofnewyork.us/resource/rbx6-tga4.json
- CSV download: https://data.cityofnewyork.us/api/views/rbx6-tga4/rows.csv?accessType=DOWNLOAD

The source schema checked during project preparation contained 46 columns.
Our extract uses 14 columns, including permit identifiers, borough, dates,
work type, ZIP code, estimated job costs, and coordinates.

Our housing measure counts permit-work-type issuance records.
It does not count completed homes or unique construction projects.

### 2. Bus Breakdown and Delays

Domain: Transportation

Dataset ID: `ez4e-fazm`

- Dataset page: https://data.cityofnewyork.us/d/ez4e-fazm
- API: https://data.cityofnewyork.us/resource/ez4e-fazm.json
- CSV download: https://data.cityofnewyork.us/api/views/ez4e-fazm/rows.csv?accessType=DOWNLOAD

The source schema checked during project preparation contained 21 columns.
Our extract uses 12 columns, including incident ID, dates, borough, reason,
delay description, and the reported number of students on the bus.

These are reported school-bus incidents. They do not represent all bus
journeys or general public transportation performance.

### Dataset counts

The notebook displays the source row counts, source column counts,
extracted row counts, and download timestamps.

The same information is saved in:

`data/processed/provenance.json`

Counts can change when the source data is refreshed. Use the counts from
the final notebook run when describing the submitted results.

### Why we paired these datasets

Both datasets contain borough information and event dates. This lets us
compare the two domains at a common borough-month level.

For example, one combined row describes permit activity and reported
school-bus incidents in Brooklyn during one month.

We use exactly two analytical datasets. No additional population or
journey-count dataset is included.

## Project workflow

1. Download the records for 2022–2024.
2. Inspect the data types, missing values, duplicates, and distributions.
3. Clean each dataset separately.
4. Aggregate records by borough, month, and category.
5. Combine the summaries at borough-month level.
6. Check the joined data for missing values and duplicate keys.
7. Answer eight research questions using charts.
8. Display the results in an interactive Dash application.

## Cleaning decisions

### Housing data

- Remove exact duplicate records.
- Exclude records with unusable dates, boroughs, or required identifiers.
- Standardize borough names, dates, categories, and ZIP codes.
- Use a composite key that includes permit identifiers, issue date,
  and work type to check duplicates.
- Exclude conflicting records with the same composite key.
- Convert invalid or negative costs to missing values.
- Flag unusually large costs using the IQR rule, but retain them because
  expensive construction work can be real.
- Set invalid coordinates to missing without removing otherwise usable rows.

### Transportation data

- Remove exact duplicates.
- Keep the most recent version when an incident ID appears more than once.
- Exclude records with unusable dates, boroughs, or missing incident IDs.
- Standardize incident categories and use UNKNOWN for missing categories.
- Parse supported delay descriptions into minutes.
- Treat unsupported descriptions and delays above 240 minutes as missing.
- Treat invalid student counts as missing while keeping the incident itself.

The delay and student-count limits are analytical cleaning rules.
They may exclude some genuine unusual cases, so the notebook documents
these limitations and includes sensitivity checks.

We do not replace missing numerical outcomes with guessed averages.

## Integration

We do not join individual permit records directly to individual bus reports.

Instead, we summarize each dataset and join on:

`borough + month`

The join checks that each source summary has only one row per key.
This avoids multiplying records during integration.

Category filters are applied within each dataset before the final
borough-month aggregation.

If a selected category has no records in an otherwise observed source-month,
its count can be zero. If an entire source-month is missing, its values stay
missing rather than being treated as zero.

Mean delay is calculated from the total valid delay and the number of valid
delay observations. It is not an average of category averages.

The integration checks include:

- Unique borough-month keys.
- Consistent date and year types.
- Counts matching the cleaned source records.
- Coverage of both datasets.
- Missing values introduced by the join.

## Research questions

| Question | Research focus | Visualization | Member |
|---|---|---|---|
| Q1 | Do borough-months with more permits also report more bus incidents? | Scatter plot | 1 |
| Q2 | Do permit and incident trends move together within each borough? | Indexed time-series chart | 1 |
| Q3 | Which seasons show higher incident reporting relative to permit activity? | Seasonal heatmap | 2 |
| Q4 | Are year-over-year changes in permits associated with changes in incidents? | Percentage-change scatter plot | 2 |
| Q5 | Is permit activity associated with incident reporting one to three months later? | Lag-correlation heatmap | 3 |
| Q6 | Are reported delays longer in high-permit months than low-permit months? | Box plot of monthly mean delays | 3 |
| Q7 | Which boroughs have a larger share of incidents than of permit activity? | Grouped share chart | 4 |
| Q8 | Does the relationship remain after removing borough and shared month effects? | Residual scatter plot | 4 |

The notebook contains the eight charts and the team's interpretations.
EDA plots are additional checks and are separate from these research charts.

## Findings and limitations

The findings depend on the downloaded snapshot and the selected filters.

See:

- The executed notebook for chart outputs and interpretations.
- `reports/FINDINGS.md` for the generated findings report.
- The dashboard's Story section for a summary of the selected data.

Important limitations include:

- Permit records are not completed homes.
- School-bus reports are not a count of all journeys.
- Incident counts are not incident rates because journey exposure is unknown.
- School schedules, borough size, and reporting changes can affect patterns.
- Borough-level analysis can hide differences between neighborhoods.
- Delay parsing leaves some reports without usable duration estimates.
- Correlation and lag patterns do not establish causation.

The results can help identify boroughs and periods for further investigation.
They should not be used alone to explain individual incidents or rank
transportation safety.

## Run the project in Google Colab

1. Open https://colab.research.google.com/
2. Upload the project's `.ipynb` notebook.
3. Save a copy to Google Drive.
4. Connect to a CPU runtime.
5. Run the cells from top to bottom.

The notebook installs packages, creates the Python files, downloads the
datasets, runs the analysis, and displays the dashboard.

No separate ZIP upload is required.

The first run downloads the data. Later runs in the same runtime can use
the cached files. Set `REFRESH = True` only when you want a new download.

Colab runtime files are temporary. Save the notebook to Drive and export
the generated project before ending the session.

To export the generated files, set `DOWNLOAD_PROJECT = True` in the final
cell and run it.

Download the executed notebook separately through:
File → Download → Download .ipynb.

## Dashboard features

The Dash application includes:

- Borough selection.
- Calendar-year selection.
- Permit work-type selection.
- Incident-reason selection.
- Search, such as `Brooklyn 2022`.
- A Generate Report button.
- Eight research charts.
- A Story section summarizing the selected data.

After changing filters, click Generate Report.

For search, click Apply Search and then Generate Report.

Some charts require enough months or observations. Narrow filters may
produce an insufficient-data message.

## Run locally

Local execution is optional if you are using Colab.

With Python installed, open a terminal in the project folder and run:

```bash
pip install -r requirements.txt
python app.py
