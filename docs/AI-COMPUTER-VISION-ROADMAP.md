# Computer-vision integration boundary

The current release does not ship a trained narcotics or contraband detector. No such detector can be responsibly claimed from a UI-only build, and a generic object detector is not evidence of criminal conduct.

A future, separately validated CV service may be connected for narrow, non-determinative evidence assistance such as image quality checks, duplicate-image detection, or detecting whether an image contains a supported non-person object class. The service should return model name/version, confidence, timestamp, and an explicit `unverified machine suggestion` label. Store model outputs as review metadata, not as case status. Human reviewers must independently assess source material. Do not use face recognition, identity inference, person tracking, risk scoring, predictive policing, or model output alone to flag, investigate, rank, or make decisions about people.

Suggested integration contract (not implemented in this release):

```json
{
  "model": "approved-model-name/version",
  "task": "bounded-image-quality-or-object-assistance",
  "result": "unverified machine suggestion",
  "confidence": 0.0,
  "review_required": true
}
```

Before integration: document lawful basis, purpose limitation, data retention, bias/error testing, security controls, operator training, appeal/correction process, and independent evaluation on representative local data.
