# Marks Card API

This API endpoint allows you to send a student's marks card as a PDF via email to both the student and their parent.

## Endpoint

```
POST /api/marks_card/
```

## Request Body

| Parameter | Type   | Required | Description              |
|-----------|--------|----------|--------------------------|
| email     | string | Yes      | Student's email address  |

## Response

Returns a success message when the marks card PDF has been sent via email.

## Example Usage

### Request

```
POST /api/marks_card/
Content-Type: application/json

{
  "email": "student1@school.com"
}
```

### Response

```json
{
  "message": "Marks card PDF sent successfully to student and parent",
  "student_email": "student1@school.com",
  "parent_emails": ["parent1@school.com"]
}
```

## How It Works

1. The API receives a student's email address in the request body
2. It retrieves the student's information and grades from the database
3. It calculates grades based on marks obtained
4. It determines pass/fail status for each subject
5. It computes overall result
6. It generates a PDF document with the marks card information
7. It sends the marks card PDF via email to both the student and their parent

## Error Handling

- If email parameter is missing: Returns 400 Bad Request
- If student is not found: Returns 404 Not Found
- If student profile is not found: Returns 404 Not Found
- If PDF generation fails: Returns 500 Internal Server Error
- If email sending fails: Returns 500 Internal Server Error