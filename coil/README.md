# COIL - Chunked Object Interchange Layer

A robust file transfer protocol for syncing large files via chunked uploads with hash verification.

## What is COIL?

COIL splits large files into chunks, uploads them with SHA

## API Endpoints

### 1. GET /api/coil-sync/status
Check upload status for a file.

**Headers:**
- `x-file-id: <file-id>` (required)

**Response:**
```json
{
  "fileId": "my-file-123",
  "chunkCount": 10,
  "chunks": {
    "0": { "hash": "abc123...", "size": 1048576 },
    "1": { "hash": "def456...", "size": 1048576 }
  }
}
```

### 2. POST /api/coil-sync/delta
Compare client chunks with server to find what needs uploading.

**Body:**
```json
{
  "fileId": "my-file-123",
  "totalExpected": 10,
  "chunks": [
    { "index": 0, "hash": "abc123..." },
    { "index": 1, "hash": "def456..." }
  ]
}
```

**Response:**
```json
{
  "needsUpload": [2, 3, 4],
  "unchanged": [0, 1],
  "missingOnServer": [2, 3, 4]
}
```

### 3. POST /api/coil-sync/upload
Upload a single chunk.

**Headers:**
- `x-file-id: <file-id>` (required)
- `x-chunk-index: <index>` (required)
- `x-hash: <sha256>` (required)
- `x-compressed: true` (optional)
- `x-original-size: <bytes>` (optional)

**Body:** Raw binary chunk data

**Response:**
```json
{
  "ok": true,
  "chunkIndex": 2,
  "hashVerified": true
}
```

### 4. POST /api/coil-sync/complete
Finalize upload and reconstruct file.

**Body:**
```json
{
  "fileId": "my-file-123",
  "originalName": "large-file.zip",
  "originalExt": ".zip",
  "totalExpected": 10
}
```

**Response:**
```json
{
  "ok": true,
  "finalHash": "sha256-of-entire-file",
  "outPath": "/path/to/reconstructed/file"
}
```