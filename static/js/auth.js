/**
 * Authentication & Session Management Module
 */

const auth = {
  currentUser: null,

  async init() {
    try {
      const data = await api.getMe();
      if (data && data.authenticated) {
        this.currentUser = data;
        this.updateNavUI();
      } else {
        this.currentUser = null;
        this.updateNavUI();
      }
    } catch (e) {
      this.currentUser = null;
      this.updateNavUI();
    }
  },

  updateNavUI() {
    const profileBtn = document.getElementById("profileBtn");
    const adminLink = document.getElementById("adminNavLink");
    const avatarBadge = document.getElementById("avatarBadge");
    const profileDropdownUsername = document.getElementById("profileDropdownUsername");
    const profileDropdownRole = document.getElementById("profileDropdownRole");
    const signinOrOutBtn = document.getElementById("signinOrOutBtn");

    if (this.currentUser) {
      if (avatarBadge) avatarBadge.textContent = this.currentUser.username[0].toUpperCase();
      if (profileDropdownUsername) profileDropdownUsername.textContent = this.currentUser.username;
      if (profileDropdownRole) profileDropdownRole.textContent = this.currentUser.role;
      if (signinOrOutBtn) signinOrOutBtn.textContent = "Sign Out";
      if (adminLink) {
        adminLink.style.display = this.currentUser.role === "admin" ? "inline-block" : "none";
      }
    } else {
      if (avatarBadge) avatarBadge.textContent = "?";
      if (profileDropdownUsername) profileDropdownUsername.textContent = "Guest Visitor";
      if (profileDropdownRole) profileDropdownRole.textContent = "Not signed in";
      if (signinOrOutBtn) signinOrOutBtn.textContent = "Sign In / Register";
      if (adminLink) adminLink.style.display = "none";
    }
  },

  showAuthModal(tab = "login") {
    const modal = document.getElementById("authModal");
    modal.classList.add("active");
    this.switchTab(tab);
  },

  hideAuthModal() {
    const modal = document.getElementById("authModal");
    modal.classList.remove("active");
  },

  switchTab(tab) {
    const loginTab = document.getElementById("tabLogin");
    const registerTab = document.getElementById("tabRegister");
    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");

    if (tab === "login") {
      loginTab.classList.add("active");
      registerTab.classList.remove("active");
      loginForm.style.display = "block";
      registerForm.style.display = "none";
    } else {
      loginTab.classList.remove("active");
      registerTab.classList.add("active");
      loginForm.style.display = "none";
      registerForm.style.display = "block";
    }
  },

  async handleLogin(identifier, password) {
    try {
      const res = await api.login(identifier, password);
      api.setToken(res.token);
      this.currentUser = res.user;
      this.updateNavUI();
      this.hideAuthModal();
      
      // If user hasn't onboarded yet, trigger onboarding genre selection
      if (!res.user.has_onboarded) {
        onboarding.show();
      } else {
        app.loadHomePage();
      }
    } catch (err) {
      alert("Login Error: " + err.message);
    }
  },

  async handleRegister(username, email, password) {
    try {
      const res = await api.register(username, email, password);
      api.setToken(res.token);
      this.currentUser = res.user;
      this.updateNavUI();
      this.hideAuthModal();
      
      // Open onboarding modal immediately after registration
      onboarding.show();
    } catch (err) {
      alert("Registration Error: " + err.message);
    }
  },

  async handleLogout() {
    try {
      await api.logout();
    } catch (e) {}
    api.setToken(null);
    this.currentUser = null;
    this.updateNavUI();
    app.loadHomePage();
  }
};
