# Attendance Generator

**An intelligent, OCR-powered system for processing and transforming attendance reports.**

Attendance Generator is a Python application designed to process PDF attendance reports through an automated, modular pipeline. It extracts information from documents, identifies their report type, converts the extracted content into structured data, applies configurable transformation strategies, and generates updated PDF and HTML reports.

The system supports two different attendance report formats and provides both a command-line workflow and a modern, browser-based user interface.

## Key Features

- **Automated OCR Processing** – Extracts text and information from PDF documents using Tesseract OCR, with support for Hebrew and English recognition.
- **Intelligent Report Classification** – Automatically identifies the report format and determines which processing strategy should be used.
- **Type-Specific Parsing** – Uses dedicated parsers and domain models for Type A and Type B reports.
- **Modular Transformation Engine** – Applies report-specific transformation strategies through a centralized transformation service.
- **Configurable Rules** – Keeps transformation parameters in a centralized settings module.
- **Dual Output Generation** – Produces both PDF and HTML versions of processed reports.
- **Modern Web Interface** – Allows users to upload PDF files, start processing, preview results, and download generated reports directly from their browser.
- **Temporary File Handling** – The web interface processes uploaded documents in a temporary workspace and keeps the internal processing directories hidden from the user.
- **Batch Processing** – Supports processing multiple PDF reports through the command-line interface.
- **Docker Support** – Provides a containerized environment with the required Python packages and system-level OCR and PDF processing dependencies.

## Application Interface

The application includes a clean, modern, Hebrew-oriented interface with right-to-left layout support.

Users can:
1. Upload an attendance report in PDF format.
2. Start the processing workflow with a single button.
3. Wait while the document is processed.
4. Preview the generated report directly in the application.
5. Download the updated report in PDF or HTML format.

The interface handles temporary files automatically, so users do not need to manage input and output folders manually.

## Processing Pipeline

The core of Attendance Generator is a modular processing pipeline:

```text
             PDF Input
                 |
                 v
          OCR Extraction
                 |
                 v
          Text Processing
                 |
                 v
        Report Classification
                 |
                 v
          Parser Factory
                 |
          +------+------+
          |             |
          v             v
       Type A         Type B
       Parser         Parser
          |             |
          +------+------+
                 |
                 v
        Structured Domain Model
                 |
                 v
       Transformation Service
                 |
          +------+------+
          |             |
          v             v
     Type A Strategy  Type B Strategy
          |             |
          +------+------+
                 |
                 v
        Transformed Report
                 |
          +------+------+
          |             |
          v             v
       HTML Output   PDF Output
```

### Pipeline Components

**1. OCR Extraction**

The system uses Tesseract OCR and PDF-to-image conversion to extract text from PDF documents. Additional OCR processing improves the recognition of important report information, including dates and summary fields.

**2. Report Classification**

The extracted text is analyzed to determine the report type. Classification uses weighted patterns designed to handle variations in OCR output.

**3. Parser Factory**

The Factory pattern selects the appropriate parser according to the detected report type.

**4. Domain Models**

The extracted information is converted into structured domain objects, separating the report data from the parsing and rendering logic.

**5. Transformation Service**

A centralized service selects the correct transformation strategy based on the report type. Each strategy handles the transformation logic for its corresponding report format.

**6. Report Generation**

The transformed domain model is passed to dedicated renderers that generate the final HTML and PDF documents.

## Supported Report Types

### Type A

Supports attendance reports containing information such as:

- Dates and weekdays
- Entry and exit times
- Work locations
- Break durations
- Regular working hours
- Overtime categories (100%, 125%, and 150%)
- Shabbat hours
- Monthly summaries and additional payments

### Type B

Supports attendance reports containing information such as:

- Dates and weekdays
- Entry and exit times
- Daily working hours
- Notes
- Monthly working-hour summaries
- Hourly rates
- Total payment information

Each report type has its own parser, domain-specific data structures, and transformation strategy.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.11 | Core application |
| Tesseract OCR | Text recognition |
| Poppler | PDF-to-image conversion |
| pdf2image | PDF processing |
| pytesseract | Python OCR integration |
| Pydantic | Structured domain models |
| python-bidi | Right-to-left text handling |
| ReportLab | PDF generation |
| Streamlit | Web application interface |
| Docker | Containerized environment |
| pytest | Automated testing |

## Project Structure

```text
AttendanceGenerator/
│
├── app.py
├── main.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .gitignore
│
├── assets/
│   └── fonts/
│
├── input/
├── output/
│
├── src/
│   ├── config/
│   │   └── settings.py
│   │
│   ├── domain/
│   │   ├── enums.py
│   │   ├── exceptions.py
│   │   └── models.py
│   │
│   ├── generation/
│   │   ├── base_renderer.py
│   │   ├── html_renderer.py
│   │   └── pdf_renderer.py
│   │
│   ├── parsing/
│   │   ├── classifier.py
│   │   ├── factory.py
│   │   ├── ocr.py
│   │   ├── parser.py
│   │   ├── type_a_parser.py
│   │   └── type_b_parser.py
│   │
│   └── transformation/
│       ├── base_strategy.py
│       ├── transformation_service.py
│       ├── type_a_strategy.py
│       └── type_b_strategy.py
│
└── tests/
    ├── test_classifier.py
    ├── test_ocr.py
    ├── test_parser_pipeline.py
    ├── test_renderer.py
    └── test_transformation.py
```

## Getting Started

### Option 1: Run with Docker (Recommended)

Docker provides the application with its required runtime environment, including Python, Tesseract OCR, Hebrew and English OCR language data, Poppler, and the Python dependencies.

This avoids the need to install these components individually on the host machine.

**Prerequisite:** Docker Desktop or Docker Engine with Docker Compose.

Build and start the application:

```bash
docker compose up --build
```

Open the application in your browser:

```text
http://localhost:8501
```

The Streamlit interface will be available locally.

### Option 2: Run Locally

#### Prerequisites

- Python 3.11
- Tesseract OCR with Hebrew and English language data
- Poppler utilities

Make sure Tesseract and Poppler are installed and available in your system PATH.

#### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/AttendanceGenerator.git
cd AttendanceGenerator
```

#### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate the environment:

**Windows:**

```powershell
.venv\Scripts\activate
```

**Linux / macOS:**

```bash
source .venv/bin/activate
```

#### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

#### 4. Start the web application

```bash
python -m streamlit run app.py
```

The application will start locally and can be accessed through your browser.

## Command-Line Processing

Attendance Generator also supports batch processing without the web interface.

1. Place PDF files inside the `input/` directory.
2. Run:

```bash
python main.py
```

3. The application will process the available PDF files and generate corresponding HTML and PDF reports in the `output/` directory.

Generated reports use a `-new` suffix to distinguish them from the original documents.

## Configuration

Transformation parameters are centralized in:

```text
src/config/settings.py
```

This module contains configurable values used by the transformation strategies, allowing behavior to be adjusted without changing the core processing pipeline.

## Testing

The project includes automated tests for its main components:

- OCR extraction
- Report classification
- Parsing pipeline
- HTML and PDF rendering
- Transformation behavior

Run the test suite with:

```bash
python -m pytest
```

## Design Principles

The project follows several software engineering principles:

- **Separation of Concerns** – OCR, classification, parsing, transformation, and rendering are handled by separate components.
- **Factory Pattern** – Selects the appropriate parser based on the detected report type.
- **Strategy Pattern** – Encapsulates report-specific transformation logic.
- **Domain-Driven Structure** – Uses dedicated domain models to represent attendance reports and their data.
- **Extensibility** – New report types and processing strategies can be added without redesigning the entire pipeline.

## Intended Use

Attendance Generator is designed for software demonstrations, testing, and synthetic attendance-data processing. Transformed reports should not be treated as authentic employment, payroll, or official attendance records.