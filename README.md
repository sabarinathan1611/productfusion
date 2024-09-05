# Multi-Tenant SaaS Authentication Service

This project is a FastAPI-based backend service for a multi-tenant SaaS application. It includes user authentication, organization management, role management, and email notifications using Brevo (formerly Sendinblue).

## Features

- **User Authentication**: Sign up, sign in, password reset with JWT tokens.
- **Organization Management**: Users can create organizations, and invite members.
- **Role Management**: Assign roles to users within an organization.
- **Statistics API**: Retrieve data about users, roles, and organizations.
- **Email Notifications**: Sends emails for sign-up, password resets, and member invitations using Brevo.

## Project Structure

```plaintext
.
├── app
│   ├── main.py           # Main application file with FastAPI routes
│   ├── email.py          # Email sending functionality using Brevo
│
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation

```

