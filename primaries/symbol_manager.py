#!/usr/bin/env python3
"""
Symbol Content Manager for TRU.
Ensures traceability and primary protection for SYMBOL channel.

Rules:
1. All symbol content must have origin metadata
2. Symbol content can never modify primary values
3. Every generated claim is traceable to its source

Usage:
  python symbol_manager.py add <claim> --source <origin>
  python symbol_manager.py list
  python symbol_manager.py audit
  python symbol_manager.py verify <claim_id>
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import sys

SYMBOL_DIR = Path("/home/workspace/primaries/symbol")
CLAIMS_FILE = SYMBOL_DIR / "symbol_claims.json"
AUDIT_LOG = SYMBOL_DIR / "symbol_audit.json"
PRIMARIES_HASH_FILE = SYMBOL_DIR / "primaries_fingerprint.json"

# Content types
CONTENT_TYPES = {
    "interpretive": "Symbolic interpretation, not verifiable",
    "generative": "Generated narrative or framework",
    "narrative": "Story or arc content",
    "speculative": "Hypothesis or projection",
    "factual_claim": "Claim about real-world state",
}

# Origin types
ORIGIN_TYPES = {
    "user_input": "Direct user statement",
    "derived": "Synthesized from primaries",
    "generative": "AI-generated content",
    "imported": "External source",
    "interpretive": "Human interpretation",
}


def generate_claim_id(claim_text, timestamp):
    """Generate unique claim ID."""
    hash_input = f"{claim_text}:{timestamp}"
    return "SYM-" + hashlib.md5(hash_input.encode()).hexdigest()[:8].upper()


def compute_primaries_fingerprint():
    """Compute hash of all primary sources to detect modifications."""
    import os
    
    primaries_files = []
    
    # SEC filings
    sec_dir = Path("/home/workspace/primaries/sec")
    if sec_dir.exists():
        for cik_dir in sec_dir.iterdir():
            if cik_dir.is_dir():
                for f in cik_dir.glob("*.json"):
                    primaries_files.append(str(f))
    
    # Temple posts
    temple_file = Path("/home/workspace/primaries/temple/temple_posts.json")
    if temple_file.exists():
        primaries_files.append(str(temple_file))
    
    # arxiv papers
    arxiv_dir = Path("/home/workspace/primaries/arxiv")
    if arxiv_dir.exists():
        for cat_dir in arxiv_dir.iterdir():
            if cat_dir.is_dir():
                for f in cat_dir.glob("*.json"):
                    primaries_files.append(str(f))
    
    # Sort for deterministic order
    primaries_files.sort()
    
    # Compute combined hash
    hasher = hashlib.sha256()
    for filepath in primaries_files:
        try:
            with open(filepath, "rb") as f:
                hasher.update(filepath.encode())
                hasher.update(f.read())
        except Exception:
            pass
    
    fingerprint = hasher.hexdigest()
    
    return {
        "fingerprint": fingerprint,
        "file_count": len(primaries_files),
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }


def check_primaries_integrity():
    """Check if primaries have been modified since last fingerprint."""
    current = compute_primaries_fingerprint()
    
    if not PRIMARIES_HASH_FILE.exists():
        # First run, save fingerprint
        with open(PRIMARIES_HASH_FILE, "w") as f:
            json.dump(current, f, indent=2)
        return {"status": "initialized", "fingerprint": current["fingerprint"][:16]}
    
    with open(PRIMARIES_HASH_FILE) as f:
        stored = json.load(f)
    
    if stored["fingerprint"] == current["fingerprint"]:
        return {"status": "integrity_ok", "fingerprint": current["fingerprint"][:16]}
    else:
        return {
            "status": "INTEGRITY_VIOLATION",
            "stored_fingerprint": stored["fingerprint"][:16],
            "current_fingerprint": current["fingerprint"][:16],
            "message": "Primary sources have been modified - potential corruption",
        }


def load_claims():
    """Load existing claims."""
    if not CLAIMS_FILE.exists():
        return []
    with open(CLAIMS_FILE) as f:
        return json.load(f)


def save_claims(claims):
    """Save claims with audit trail."""
    with open(CLAIMS_FILE, "w") as f:
        json.dump(claims, f, indent=2)
    
    # Log the save
    log_audit("claims_saved", {"count": len(claims)})


def log_audit(action, details):
    """Log audit event."""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "details": details,
    }
    
    logs = []
    if AUDIT_LOG.exists():
        with open(AUDIT_LOG) as f:
            logs = json.load(f)
    
    logs.append(log_entry)
    
    # Keep last 1000 entries
    if len(logs) > 1000:
        logs = logs[-1000:]
    
    with open(AUDIT_LOG, "w") as f:
        json.dump(logs, f, indent=2)


def add_claim(claim_text, source, content_type="interpretive", origin="user_input"):
    """Add a new symbol claim with traceability."""
    
    # Check primaries integrity first
    integrity = check_primaries_integrity()
    if integrity["status"] == "INTEGRITY_VIOLATION":
        print(f"ERROR: {integrity['message']}")
        return None
    
    timestamp = datetime.now(timezone.utc).isoformat()
    claim_id = generate_claim_id(claim_text, timestamp)
    
    # Build claim with full traceability
    claim = {
        "claim_id": claim_id,
        "claim": claim_text,
        "category": content_type,
        "verdict": "pending",
        "type": content_type,
        "origin": {
            "type": origin,
            "source": source,
            "timestamp": timestamp,
        },
        "traceability": {
            "added_at": timestamp,
            "added_by": "symbol_manager",
            "primaries_fingerprint": integrity.get("fingerprint", "unknown"),
            "modified": False,
            "modification_history": [],
        },
        "protection": {
            "can_modify_primaries": False,
            "is_primary": False,
            "channel": "SYMBOL",
        },
    }
    
    # Load existing claims
    claims = load_claims()
    claims.append(claim)
    save_claims(claims)
    
    # Log addition
    log_audit("claim_added", {
        "claim_id": claim_id,
        "claim_preview": claim_text[:100],
        "origin": origin,
        "source": source,
    })
    
    print(f"[symbol] added claim {claim_id}")
    print(f"  origin: {origin}")
    print(f"  source: {source}")
    print(f"  primaries fingerprint: {claim['traceability']['primaries_fingerprint']}")
    
    return claim


def list_claims():
    """List all symbol claims with traceability."""
    claims = load_claims()
    
    print(f"Symbol Claims: {len(claims)}\n")
    
    for c in claims:
        origin = c.get("origin", {})
        trace = c.get("traceability", {})
        
        modified_flag = " [MODIFIED]" if trace.get("modified") else ""
        print(f"  [{c['claim_id']}] {c['claim'][:60]}{modified_flag}")
        print(f"      origin: {origin.get('type', '?')} from {origin.get('source', '?')[:30]}")
        print(f"      fingerprint: {trace.get('primaries_fingerprint', '?')}")
        if trace.get("modification_history"):
            print(f"      modifications: {len(trace['modification_history'])}")
        print()


def audit():
    """Run full audit of symbol content and primary integrity."""
    print("[audit] checking primaries integrity...")
    integrity = check_primaries_integrity()
    print(f"  status: {integrity['status']}")
    print(f"  fingerprint: {integrity.get('fingerprint', 'N/A')}")
    
    if integrity["status"] == "INTEGRITY_VIOLATION":
        print("\n  ⚠️  ALERT: Primary sources have been modified!")
        print(f"  Stored: {integrity.get('stored_fingerprint')}")
        print(f"  Current: {integrity.get('current_fingerprint')}")
    
    print("\n[audit] checking symbol claims...")
    claims = load_claims()
    
    issues = []
    
    for c in claims:
        # Check for missing traceability
        if "origin" not in c:
            issues.append({
                "claim_id": c.get("claim_id", "unknown"),
                "issue": "missing_origin",
                "severity": "high",
            })
        
        if "traceability" not in c:
            issues.append({
                "claim_id": c.get("claim_id", "unknown"),
                "issue": "missing_traceability",
                "severity": "high",
            })
        
        # Check for primary modification attempts
        protection = c.get("protection", {})
        if protection.get("can_modify_primaries") == True:
            issues.append({
                "claim_id": c.get("claim_id", "unknown"),
                "issue": "illegal_primary_modification_flag",
                "severity": "critical",
            })
        
        if protection.get("is_primary") == True:
            issues.append({
                "claim_id": c.get("claim_id", "unknown"),
                "issue": "symbol_marked_as_primary",
                "severity": "critical",
            })
    
    print(f"  claims: {len(claims)}")
    print(f"  issues: {len(issues)}")
    
    if issues:
        print("\n  Issues found:")
        for issue in issues:
            print(f"    [{issue['severity'].upper()}] {issue['claim_id']}: {issue['issue']}")
    
    # Summary
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "primaries_integrity": integrity["status"],
        "total_claims": len(claims),
        "total_issues": len(issues),
        "critical_issues": len([i for i in issues if i["severity"] == "critical"]),
        "issues": issues,
    }
    
    # Save audit report
    audit_file = SYMBOL_DIR / "last_audit.json"
    with open(audit_file, "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n[audit] report saved to {audit_file}")
    
    return summary


def migrate():
    """Migrate existing claims to add traceability metadata."""
    if not CLAIMS_FILE.exists():
        print("[migrate] no claims file found")
        return
    
    print("[migrate] migrating claims...")
    
    with open(CLAIMS_FILE) as f:
        claims = json.load(f)
    
    # Add traceability to existing claims
    for claim in claims:
        if "traceability" not in claim:
            claim["traceability"] = {
                "added_at": datetime.now(timezone.utc).isoformat(),
                "added_by": "symbol_manager",
                "primaries_fingerprint": "unknown",
                "modified": False,
                "modification_history": [],
            }
        if "origin" not in claim:
            claim["origin"] = {
                "type": "unknown",
                "source": "unknown",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        if "protection" not in claim:
            claim["protection"] = {
                "can_modify_primaries": False,
                "is_primary": False,
                "channel": "SYMBOL",
            }
    
    save_claims(claims)
    log_audit("claims_migrated", {"count": len(claims)})


def verify_claim(claim_id):
    """Verify a specific claim's traceability."""
    claims = load_claims()
    
    for c in claims:
        if c.get("claim_id") == claim_id:
            print(f"Claim: {c['claim'][:80]}\n")
            
            origin = c.get("origin", {})
            print(f"Origin:")
            print(f"  Type: {origin.get('type', 'MISSING')}")
            print(f"  Source: {origin.get('source', 'MISSING')}")
            print(f"  Timestamp: {origin.get('timestamp', 'MISSING')}")
            
            trace = c.get("traceability", {})
            print(f"\nTraceability:")
            print(f"  Added: {trace.get('added_at', 'MISSING')}")
            print(f"  By: {trace.get('added_by', 'MISSING')}")
            print(f"  Fingerprint: {trace.get('primaries_fingerprint', 'MISSING')}")
            print(f"  Modified: {trace.get('modified', False)}")
            
            protection = c.get("protection", {})
            print(f"\nProtection:")
            print(f"  Can modify primaries: {protection.get('can_modify_primaries', 'N/A')}")
            print(f"  Is primary: {protection.get('is_primary', 'N/A')}")
            print(f"  Channel: {protection.get('channel', 'MISSING')}")
            
            # Check integrity
            if trace.get("primaries_fingerprint"):
                current = compute_primaries_fingerprint()
                if trace["primaries_fingerprint"] == current["fingerprint"][:16]:
                    print(f"\n✓ Primaries fingerprint matches current state")
                else:
                    print(f"\n⚠️ Primaries fingerprint mismatch - primaries modified since claim added")
            
            return c
    
    print(f"Claim {claim_id} not found")
    return None


def protect_primaries(operation, claim_id, proposed_changes):
    """Gatekeeper for primary modifications - should always reject."""
    
    log_audit("primary_modification_attempt", {
        "operation": operation,
        "claim_id": claim_id,
        "proposed_changes": proposed_changes,
        "result": "REJECTED",
    })
    
    print(f"[protection] REJECTED: Symbol content cannot modify primaries")
    print(f"  claim: {claim_id}")
    print(f"  operation: {operation}")
    
    return {
        "allowed": False,
        "reason": "Symbol content is prohibited from modifying TRUTH channel primaries",
        "policy": "never_modify_primary_values",
    }


if __name__ == "__main__":
    SYMBOL_DIR.mkdir(parents=True, exist_ok=True)
    
    cmd = sys.argv[1] if len(sys.argv) > 1 else "audit"
    
    if cmd == "add":
        if len(sys.argv) < 4:
            print("Usage: python symbol_manager.py add <claim> --source <origin>")
            sys.exit(1)
        
        claim_text = sys.argv[2]
        source = sys.argv[4] if len(sys.argv) > 4 else "unknown"
        add_claim(claim_text, source)
    
    elif cmd == "list":
        list_claims()
    
    elif cmd == "audit":
        audit()
    
    elif cmd == "verify":
        if len(sys.argv) < 3:
            print("Usage: python symbol_manager.py verify <claim_id>")
            sys.exit(1)
        verify_claim(sys.argv[2])
    
    elif cmd == "fingerprint":
        fp = compute_primaries_fingerprint()
        print(f"Primaries fingerprint: {fp['fingerprint'][:16]}")
        print(f"File count: {fp['file_count']}")
    
    elif cmd == "migrate":
        migrate()
    
    else:
        print(f"Unknown command: {cmd}")
