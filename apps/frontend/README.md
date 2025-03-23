# MediaWhisperer Frontend

## Setup

1. Install dependencies:

```bash
npm install
```

2. Run the development server:

```bash
npm run dev
```

The frontend will be available at http://localhost:3000

## Build for Production

```bash
npm run build
npm start
```

## Configuration

Create a `.env.local` file with the following environment variables:

```
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key
NEXT_PUBLIC_API_URL=http://localhost:8000
```
