# Frappe Webshop

Frappe webshop is an Open Source eCommerce Platform
![Frappe Webshop](webshop.png)

## Update guide

**Note:** There will be no commit on `develop` branch.

There are 2 remotes:

- origin (zaviagodev/webshop)
- upstream (frappe/webshop)

Each version should have a seprate branch on both remotes like `version-15`, `version-13` e.t.c

### Steps

1. Developer will commit the change in the relative branch example `version-15`
2. After commiting developer should keep the relative branch in sync with its `upstream` branch by:

   ```bash
   git fetch upstream
   git merge upstream/<relative branch>
   ```

3. At times there might be some conflicts developer hast to make sure the conflicts are resolved properly.

### Steps for new version Release

1. Switch to latest branch example `version-15` & make sure its synced with its upstream branch.

   ```bash
   git checkout version-15
   git fetch upstream
   git merge upstream/version-15
   ```

2. create new branch from latest branch & push.

   ```bash
   git checkout version-15
   git checkout -b version-16
   git push origin version-16
   ```

3. sync with relative upstream branch by

   ```bash
   git fetch upstream version-16
   git merge upstream/version-16
   ```

4. resolve conflicts if any & push.

   ```bash
   git push origin version-16
   ```
