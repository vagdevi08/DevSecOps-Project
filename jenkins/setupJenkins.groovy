import jenkins.model.*
import hudson.security.*
import jenkins.security.s2m.AdminWhitelistRule
import hudson.security.csrf.DefaultCrumbIssuer

def instance = Jenkins.get()

// ----------------------
// Disable master kill switch
// ----------------------
println "--> Disabling master kill switch"
instance.getInjector().getInstance(AdminWhitelistRule.class)
    .setMasterKillSwitch(false)

// ----------------------
// Set Jenkins URL from env var
// ----------------------
def env = System.getenv()
def jenkinsURL = "http://${env['JenkinsPublicHostname'] ?: 'localhost'}:8080/"
println "--> Setting Jenkins URL to ${jenkinsURL}"
JenkinsLocationConfiguration.get().with {
    setUrl(jenkinsURL)
    save()
}

// ----------------------
// Enable CSRF protection
// ----------------------
println "--> Enabling CSRF protection"
instance.setCrumbIssuer(new DefaultCrumbIssuer(true))
instance.save()

// ----------------------
// Set up security realm
// ----------------------
println "--> Setting up security realm and admin user"

if (!(instance.getSecurityRealm() instanceof HudsonPrivateSecurityRealm)) {
    instance.setSecurityRealm(new HudsonPrivateSecurityRealm(false))
}

if (!(instance.getAuthorizationStrategy() instanceof GlobalMatrixAuthorizationStrategy)) {
    instance.setAuthorizationStrategy(new GlobalMatrixAuthorizationStrategy())
}

def username = "myjenkins"
def password = env['Jenkins_PW'] ?: "admin"  // Fallback for dev/test

def user = instance.getSecurityRealm().getUser(username)
if (user == null) {
    println "--> Creating user '${username}'"
    user = instance.getSecurityRealm().createAccount(username, password)
    user.save()
} else {
    println "--> User '${username}' already exists"
}

instance.getAuthorizationStrategy().add(Jenkins.ADMINISTER, username)
instance.save()

println "--> Jenkins setup complete"
