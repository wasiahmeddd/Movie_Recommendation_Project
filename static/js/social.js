/**
 * Social Recommendations & Friends Module
 * Handles contact picker API investigation with graceful fallback to username search.
 */

const social = {
  async loadFriendsView() {
    const listContainer = document.getElementById("friendsListContainer");
    const contactsBanner = document.getElementById("contactsApiNotice");

    // Check Contact Picker API support
    if ("contacts" in navigator && "ContactsManager" in window) {
      if (contactsBanner) {
        contactsBanner.innerHTML = `
          <div style="background: rgba(70, 211, 105, 0.15); border: 1px solid var(--accent-green); padding: 12px; border-radius: 6px; margin-bottom: 16px;">
            <strong>📱 Device Contacts Supported:</strong> You can import friends from your device contacts.
            <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 12px; margin-left: 10px;" onclick="social.requestDeviceContacts()">Access Contacts</button>
          </div>
        `;
      }
    } else {
      if (contactsBanner) {
        contactsBanner.innerHTML = `
          <div style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); padding: 10px 14px; border-radius: 6px; margin-bottom: 16px; font-size: 12px; color: var(--text-secondary);">
            ℹ️ Native Contact Picker API is not available on this desktop browser. Use the instant username search below.
          </div>
        `;
      }
    }

    try {
      const friends = await api.getFriends();
      if (!listContainer) return;

      if (!friends || friends.length === 0) {
        listContainer.innerHTML = `<p style="color: var(--text-muted); font-size: 14px;">No friends connected yet. Search users above to connect and share recommendations!</p>`;
        return;
      }

      listContainer.innerHTML = friends.map(f => `
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px; background: #222; border-radius: 6px; margin-bottom: 10px;">
          <div style="display: flex; align-items: center; gap: 12px;">
            <div style="width: 38px; height: 38px; border-radius: 50%; background: #e50914; display: flex; align-items: center; justify-content: center; font-weight: bold;">
              ${f.username[0].toUpperCase()}
            </div>
            <div>
              <div style="font-weight: 600; font-size: 14px;">${f.username}</div>
              <div style="font-size: 12px; color: var(--text-secondary);">
                ${f.last_watched_movie ? `Recently watched: <span style="color: #fff;">${f.last_watched_movie}</span>` : 'Connected Friend'}
              </div>
            </div>
          </div>
          <span style="font-size: 11px; background: rgba(70, 211, 105, 0.2); color: var(--accent-green); padding: 4px 8px; border-radius: 4px; font-weight: 600;">
            Connected
          </span>
        </div>
      `).join("");
    } catch (e) {
      if (listContainer) listContainer.innerHTML = `<p style="color: #ff6b6b;">Error loading friends: ${e.message}</p>`;
    }
  },

  async handleSearch(query) {
    const resultsContainer = document.getElementById("friendSearchResults");
    if (!query || query.length < 2) {
      resultsContainer.innerHTML = "";
      return;
    }

    try {
      const results = await api.searchFriends(query);
      if (!results || results.length === 0) {
        resultsContainer.innerHTML = `<p style="color: var(--text-muted); font-size: 13px; padding: 8px;">No users found matching "${query}".</p>`;
        return;
      }

      resultsContainer.innerHTML = results.map(u => `
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px; background: #2a2a2a; border-radius: 4px; margin-bottom: 6px;">
          <span style="font-weight: 600; font-size: 13px;">${u.username}</span>
          ${u.connection_status === 'friends' ? 
            `<span style="font-size: 11px; color: var(--accent-green);">Friend</span>` :
            `<button class="btn btn-secondary" style="padding: 4px 10px; font-size: 12px;" onclick="social.addFriend(${u.id})">+ Connect</button>`
          }
        </div>
      `).join("");
    } catch (err) {
      resultsContainer.innerHTML = `<p style="color: #ff6b6b; font-size: 12px;">Search failed</p>`;
    }
  },

  async addFriend(userId) {
    try {
      await api.sendFriendRequest(userId);
      alert("Friend connected successfully!");
      this.loadFriendsView();
      const input = document.getElementById("friendSearchInput");
      if (input) {
        this.handleSearch(input.value);
      }
    } catch (e) {
      alert("Failed to connect: " + e.message);
    }
  },

  async requestDeviceContacts() {
    try {
      const props = ["name", "email", "tel"];
      const opts = { multiple: true };
      const contacts = await navigator.contacts.select(props, opts);
      alert(`Selected ${contacts.length} device contacts. Matching with registered users...`);
    } catch (ex) {
      alert("Contact selection cancelled or not permitted: " + ex.message);
    }
  }
};
