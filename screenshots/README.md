# Screenshot Checklist

Use this folder to store screenshots for the lab submission. Recommended filenames are listed below so the grading evidence is easy to review.

## Required Base Evidence

1. `01-pytest-pass.png`
   - Show terminal output from:
   ```powershell
   python -m pytest -q
   ```
   - Expected: `14 passed`.
   - Results:
   ```powershell
                                                                           [100%] 
    ======================================== warnings summary =========================================
    .venv\Lib\site-packages\fastmcp\server\auth\providers\jwt.py:10
      D:\AI_IN_ACTION\LAB\Asg26\Day26-Track3-MCP-tool-integration\.venv\Lib\site-packages\fastmcp\server\auth\providers\jwt.py:10: AuthlibDeprecationWarning: authlib.jose module is deprecated, please use joserfc instead.
      It will be compatible before version 2.0.0.
        from authlib.jose import JsonWebKey, JsonWebToken

    -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
    14 passed, 1 warning in 4.97s
      ```

    2. `02-verify-server-pass.png`
      - Show terminal output from:
      ```powershell
      python implementation\verify_server.py
      ```
      - Expected: `DISCOVERY`, successful tool calls, invalid error, and `Verification passed`.
      - Results:
      ```powershell
      DISCOVERY
    {
      "resource_templates": [
        "schema://table/{table_name}"
      ],
      "resources": [
        "schema://database"
      ],
      "tools": [
        "search",
        "insert",
        "aggregate"
      ]
    }

    SEARCH cohort A1
    {
      "annotations": {
        "backend": "SQLiteAdapter",
        "filter_count": 1,
        "order_direction": "desc",
        "ordered_by": "score",
        "selected_columns": 4
      },
      "columns": [
        "id",
        "name",
        "cohort",
        "score"
      ],
      "count": 3,
      "filters": [
        {
          "column": "cohort",
          "op": "=",
          "value": "A1"
        }
      ],
      "limit": 3,
      "offset": 0,
      "ok": true,
      "pagination": {
        "has_more": false,
        "limit": 3,
        "next_offset": null,
        "offset": 0,
        "returned": 3
      },
      "rows": [
        {
          "cohort": "A1",
          "id": 5,
          "name": "Emma Vo",
          "score": 95.0
        },
        {
          "cohort": "A1",
          "id": 1,
          "name": "An Nguyen",
          "score": 91.5
        },
        {
          "cohort": "A1",
          "id": 2,
          "name": "Binh Tran",
          "score": 84.0
        }
      ],
      "table": "students"
    }

    INSERT student
    {
      "annotations": {
        "backend": "SQLiteAdapter",
        "inserted_columns": [
          "name",
          "cohort",
          "email",
          "score"
        ],
        "primary_key": "id"
      },
      "inserted": {
        "cohort": "C3",
        "email": "minh.ho+933f16ea@example.edu",
        "id": 6,
        "name": "Minh Ho",
        "score": 81.0
      },
      "ok": true,
      "table": "students"
    }

    AGGREGATE avg score by cohort
    {
      "annotations": {
        "backend": "SQLiteAdapter",
        "filter_count": 0,
        "grouped": true
      },
      "column": "score",
      "filters": [],
      "group_by": "cohort",
      "metric": "avg",
      "ok": true,
      "rows": [
        {
          "group_value": "A1",
          "value": 90.16666666666667
        },
        {
          "group_value": "B2",
          "value": 82.75
        },
        {
          "group_value": "C3",
          "value": 81.0
        }
      ],
      "table": "students"
    }

    INVALID search
    {
      "error": "unknown table 'missing_table'; available tables: courses, enrollments, students",
      "error_type": "validation_error",
      "ok": false
    }

    SCHEMA resource count
    {
      "schema_contents": 1
    }

    TABLE schema resource count
    {
      "schema_contents": 1
    }

    Verification passed.
   ```

3. `03-inspector-tools.png`
   - Show MCP Inspector connected to the server.
   - The tools list must show `search`, `insert`, and `aggregate`.

4. `04-inspector-resources.png`
   - Show MCP Inspector resources.
   - Must show `schema://database` and `schema://table/{table_name}`.
   - Results:
      -  `schema://database`:
      ```json
      {
      "contents": [
         {
            "uri": "schema://database",
            "mimeType": "application/json",
            "text": "{\"database\":\"D:\\\\AI_IN_ACTION\\\\LAB\\\\Asg26\\\\Day26-Track3-MCP-tool-integration\\\\implementation\\\\lab.db\",\"backend\":\"SQLiteAdapter\",\"tables\":{\"courses\":{\"columns\":[{\"name\":\"id\",\"type\":\"INTEGER\",\"nullable\":true,\"default\":null,\"primary_key\":true},{\"name\":\"code\",\"type\":\"TEXT\",\"nullable\":false,\"default\":null,\"primary_key\":false},{\"name\":\"title\",\"type\":\"TEXT\",\"nullable\":false,\"default\":null,\"primary_key\":false},{\"name\":\"credits\",\"type\":\"INTEGER\",\"nullable\":false,\"default\":null,\"primary_key\":false}]},\"enrollments\":{\"columns\":[{\"name\":\"id\",\"type\":\"INTEGER\",\"nullable\":true,\"default\":null,\"primary_key\":true},{\"name\":\"student_id\",\"type\":\"INTEGER\",\"nullable\":false,\"default\":null,\"primary_key\":false},{\"name\":\"course_id\",\"type\":\"INTEGER\",\"nullable\":false,\"default\":null,\"primary_key\":false},{\"name\":\"grade\",\"type\":\"REAL\",\"nullable\":false,\"default\":null,\"primary_key\":false},{\"name\":\"status\",\"type\":\"TEXT\",\"nullable\":false,\"default\":\"'active'\",\"primary_key\":false}]},\"students\":{\"columns\":[{\"name\":\"id\",\"type\":\"INTEGER\",\"nullable\":true,\"default\":null,\"primary_key\":true},{\"name\":\"name\",\"type\":\"TEXT\",\"nullable\":false,\"default\":null,\"primary_key\":false},{\"name\":\"cohort\",\"type\":\"TEXT\",\"nullable\":false,\"default\":null,\"primary_key\":false},{\"name\":\"email\",\"type\":\"TEXT\",\"nullable\":false,\"default\":null,\"primary_key\":false},{\"name\":\"score\",\"type\":\"REAL\",\"nullable\":false,\"default\":null,\"primary_key\":false}]}}}"
         }
      ]
      }
      ```
      -  `schema://table/{table_name}`
      ```json
      {
      "contents": [
         {
            "uri": "schema://table/students",
            "mimeType": "application/json",
            "text": "{\"table\":\"students\",\"columns\":[{\"name\":\"id\",\"type\":\"INTEGER\",\"nullable\":true,\"default\":null,\"primary_key\":true},{\"name\":\"name\",\"type\":\"TEXT\",\"nullable\":false,\"default\":null,\"primary_key\":false},{\"name\":\"cohort\",\"type\":\"TEXT\",\"nullable\":false,\"default\":null,\"primary_key\":false},{\"name\":\"email\",\"type\":\"TEXT\",\"nullable\":false,\"default\":null,\"primary_key\":false},{\"name\":\"score\",\"type\":\"REAL\",\"nullable\":false,\"default\":null,\"primary_key\":false}]}"
         }
      ]
      }
      ```

5. `05-search-tool-result.png`
   - Show a successful `search` call.
   - Include rows plus `pagination` and `annotations`.

6. `06-insert-tool-result.png`
   - Show a successful `insert` call.
   - Include inserted payload with generated `id`.

7. `07-aggregate-tool-result.png`
   - Show a successful `aggregate` call.
   - Example: average `score` grouped by `cohort`.

8. `08-invalid-request-error.png`
   - Show invalid request handling.
   - Example `search` with:
   ```json
   {"table": "missing_table"}
   ```
   - Expected: `ok=false` and clear unknown table error.

## Bonus Evidence

9. `09-http-auth-401.png`
   - Show HTTP auth rejecting a request without bearer token.
   - Expected terminal/server log: `401 Unauthorized` or `invalid_token`.

10. `10-http-auth-token-success.png`
    - Show an authenticated HTTP client call with token `sqlite-lab-secret`.
    - Expected: list of tools or successful tool call.

11. `11-postgres-backend.png`
    - Show `verify_server.py` output while `.env` uses `DATABASE_URL`.
    - Must include:
    ```json
    "backend": "PostgresAdapter"
    ```

## Notes

- Do not include `.env` screenshots if it shows a real password.
- If you need to show `.env`, blur or hide the password in `DATABASE_URL`.
- For final submission, screenshots plus the demo video are enough; this folder is for organized evidence.

