# Scenario: app-services-bootstrap

## Case 1

**Prompt:** Set up services for a new mobile game.

**Expected:** Builds the status table (service, tag Reference/Studio addition/Optional, location, skill, status, evidence), installs in the install order, framework modules first.

**Must not:** Writes custom services before checking the installed package or calls SDKs from gameplay code.

## Case 2

**Prompt:** Ads must not start before consent.

**Expected:** Follows install order: consent and remote defaults before ads; IAP only after catalog and receiver.

**Must not:** Initialises ads first and fixes consent later.

## Case 3

**Prompt:** Remote config is unreachable on first launch.

**Expected:** Every remote value has a local default; the game is correct offline.

**Must not:** Blocks startup waiting for the fetch.

## Case 4

**Prompt:** Verification pass.

**Expected:** Greps that no SDK call exists outside facades and that services are scene-authored children of the root prefab.

**Must not:** Reports done without the grep evidence.
