# StreamMate AI Callback Handler

iPaymu payment callback handler for StreamMate AI application.

## Environment Variables

Set these in your deployment platform:

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role key
- `IPAYMU_MERCHANT_KEY`: Your iPaymu merchant key
- `IPAYMU_API_KEY`: Your iPaymu API key

## Endpoints

- `POST /ipaymu-callback`: Handles iPaymu payment callbacks
- `GET /payment-completed`: Payment completion page
- `GET /healthz`: Health check endpoint

## Deployment

This is designed to be deployed on Render, Railway, or similar platforms. 