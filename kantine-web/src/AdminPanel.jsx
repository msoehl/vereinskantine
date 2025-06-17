import { useEffect, useState } from "react";

function Login({ setLoggedIn, setView }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  

  useEffect(() => {
    if (!localStorage.getItem("admin_password")) {
      localStorage.setItem("admin_password", "admin");
    }
  }, []);

  const handleLogin = () => {
    const adminPassword = localStorage.getItem("admin_password");

    if (
      (username === "admin" && password === adminPassword) ||
      (username === localStorage.getItem("username") && password === localStorage.getItem("user_password"))
    ) {
      localStorage.setItem("loggedIn", "true");
      localStorage.setItem("currentUser", username);
      setLoggedIn(true);
      setView("products")
    } else {
      setError("Falscher Benutzername oder Passwort.");
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      handleLogin();
    }
  };

  return (
    <div className="login-container">
      <div className="grid gap-4 p-4">
        <h1 className="text-2xl font-bold">Login</h1>
        <input
          className="p-2 border rounded"
          placeholder="Benutzername"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <input
          className="p-2 border rounded"
          placeholder="Passwort"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button onClick={handleLogin}>Login</button>
        {error && <div className="text-red-500 font-semibold">{error}</div>}
      </div>
    </div>
  );
}

function UtcClock() {
  const [utcTime, setUtcTime] = useState(() => formatUtc(new Date()));

  useEffect(() => {
    const interval = setInterval(() => {
      setUtcTime(formatUtc(new Date()));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  function formatUtc(date) {
    const iso = date.toISOString();
    return iso.split(".")[0].replace("T", " ");
  }

  return (
    <div style={{ fontSize: "14px", fontWeight: "bold", textAlign: "center", marginBottom: "10px" }}>
      Aktuelle UTC-Zeit: {utcTime}
    </div>
  );
}

export default function AdminPanel() {
  const [loggedIn, setLoggedIn] = useState(() => localStorage.getItem("loggedIn") === "true");
  const [view, setView] = useState("products");
  const [selectedMonth, setSelectedMonth] = useState(() => { const now = new Date(); return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;});
  const [useVFL, setUseVFL] = useState(() => { return localStorage.getItem("vflEnabled") === "true";});
  const [products, setProducts] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [users, setUsers] = useState([]);
  const [name, setName] = useState("");
  const [price, setPrice] = useState("");
  const [vflArticleId, setVflArticleId] = useState("");
  const [salestax, setSalestax] = useState("7");
  const [category, setCategory] = useState("");
  const [username, setUsername] = useState("");
  const [rfid, setRfid] = useState("");
  const [vfMemberid, setVfMemberid] = useState("");
  const [userPassword, setUserPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordMessage, setPasswordMessage] = useState("");
  const [passwordSuccess, setPasswordSuccess] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [editName, setEditName] = useState("");
  const [editPrice, setEditPrice] = useState("");
  const [editCategory, setEditCategory] = useState("");
  const [editingUser, setEditingUser] = useState(null);
  const [editUsername, setEditUsername] = useState("");
  const [editRfid, setEditRfid] = useState("");
  const [editPassword, setEditPassword] = useState("");
  const [editVfMemberid, setEditVfMemberid] = useState("");
  const [editVflArticleId, setEditVflArticleId] = useState("");
  const [editSalestax, setEditSalestax] = useState("");

  



  useEffect(() => {
  const currentUser = localStorage.getItem("currentUser");
  if (!loggedIn || !currentUser) return;
    let timeout;
    const logoutAfterInactivity = () => {
      localStorage.removeItem("loggedIn");
      localStorage.removeItem("currentUser");
      setLoggedIn(false);
      alert("Sie wurden aufgrund von Inaktivität ausgeloggt.");
    };

    const resetTimer = () => {
      clearTimeout(timeout);
      timeout = setTimeout(logoutAfterInactivity, 10 * 60 * 1000);
    };

    const activityEvents = ["mousemove", "keydown", "click", "scroll"];

    activityEvents.forEach(event =>
      window.addEventListener(event, resetTimer)
    );

    resetTimer();

    return () => {
      clearTimeout(timeout);
      activityEvents.forEach(event =>
        window.removeEventListener(event, resetTimer)
      );
    };
  }, [loggedIn]);

  const toggleVfl = () => {
    const newValue = !useVFL;
    setUseVFL(newValue);
    localStorage.setItem("vflEnabled", String(newValue));

    fetch("/vfl-settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ vfl_enabled: newValue }),
    });
  };

  const importUsers = async () => {
    const res = await fetch("/import-users", { method: "POST" });
    if (res.ok) {
      const result = await res.json();
      alert(`${result.imported.length} Benutzer importiert.`);
      fetchUsers();
    } else {
      alert("Fehler beim Import.");
    }
  };

  const exportTransactions = () => {
    if (!Array.isArray(transactions)) return;
    const header = ["Transaktion-ID", "Benutzer-ID", "Summe", "Datum", "Produkte"];
    const rows = transactions.map(t => [
      t.id,
      t.user_id,
      t.total.toFixed(2) + " €",
      new Date(t.timestamp).toLocaleString(),
      t.items.map(i => `${i.product_name} (€${i.price.toFixed(2)})`).join(" / ")
    ]);
    const csvContent = [header, ...rows].map(e => e.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(";")).join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "transaktionen.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const syncProducts = async () => {
    const res = await fetch("/sync/articles", { method: "POST" });
    if (res.ok) {
    const result = await res.json();
    alert(result.message);
    fetchProducts();
  } else {
    alert("Fehler beim Synchronisieren.");
  }
  };

  const fetchProducts = async () => {
    const res = await fetch("/products");
    const data = await res.json();
    setProducts(data);
  };

  const fetchTransactions = async () => {
    const res = await fetch("/transactions");
    const data = await res.json();
    setTransactions(data);
  };

const startEditProduct = (product) => {
  setEditingProduct(product);
  setEditName(product.name);
  setEditPrice(product.price.toString());
  setEditCategory(product.category);
  setEditVflArticleId(product.vfl_articleid || "");
  setEditSalestax(product.salestax?.toString() || "7");
};

const saveProductEdit = async () => {
  if (!editName || !editPrice || !editCategory) {
  alert("Bitte alle Felder beim Produkt bearbeiten ausfüllen.");
  return;
}
  await fetch(`/products/${editingProduct.id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: editName,
      price: parseFloat(editPrice),
      category: editCategory,
      vfl_articleid: editVflArticleId,
      salestax: parseFloat(editSalestax),
    }),
  });
  setEditingProduct(null);
  fetchProducts();
};


  const deleteProduct = async (id) => {
    await fetch(`/products/${id}`, { method: "DELETE" });
    fetchProducts();
  };

  const deleteUser = async (id) => {
    await fetch(`/users/${id}`, { method: "DELETE" });
    fetchUsers();
  };

  const fetchUsers = async () => {
    const res = await fetch("/users");
    const data = await res.json();
    setUsers(data);
  };

const filteredTransactions = selectedMonth
  ? transactions.filter(t => {
      const date = new Date(t.timestamp);
      const yearMonth = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
      return yearMonth === selectedMonth;
    })
  : transactions;

const startEditUser = (user) => {
  setEditingUser(user);
  setEditUsername(user.username);
  setEditRfid(user.rfid);
  setEditPassword("");
  setEditVfMemberid(user.vf_memberid || "");
};

const saveUserEdit = async () => {
  if (!editUsername || !editRfid) {
  alert("Bitte Benutzername und RFID eingeben.");
  return;
}
  const payload = {
    username: editUsername,
    rfid: editRfid,
    vf_memberid: parseInt(editVfMemberid) || null
  };
  if (editPassword.trim() !== "") {
    payload.password = editPassword;
  }

  await fetch(`/users/${editingUser.id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  setEditingUser(null);
  fetchUsers();
};


const addProduct = async () => {
  if (!name || !price || !category) {
    alert("Bitte alle Produktfelder ausfüllen.");
    return;
  }

  const priceNumber = parseFloat(price);
  if (isNaN(priceNumber) || priceNumber < 0) {
    alert("Bitte einen gültigen Preis angeben.");
    return;
  }

  const res = await fetch("/products", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, price: priceNumber, category,  vfl_articleid: vflArticleId, salestax: parseFloat(salestax), })
  });

  if (!res.ok) {
    alert("Fehler beim Speichern des Produkts.");
    return;
  }

  setName("");
  setPrice("");
  setCategory("");
  fetchProducts();
};

  const addUser = async () => {
    if (!username || !rfid || !userPassword) {
      alert("Bitte alle Benutzerfelder ausfüllen.");
      return;
    }

    const res = await fetch("/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, rfid, password: userPassword, vf_memberid: parseInt(vfMemberid) })
    });

    if (!res.ok) {
      alert("Fehler beim Anlegen des Benutzers.");
      return;
    }

  localStorage.setItem("username", username);
  localStorage.setItem("user_password", userPassword);
  setUsername("");
  setRfid("");
  setUserPassword("");
  fetchUsers();
};


  const changePassword = () => {
    const currentUser = localStorage.getItem("currentUser");
    if (!userPassword || !confirmPassword) {
      setPasswordMessage("Bitte beide Felder ausfüllen.");
      setPasswordSuccess(false);
      return;
    }
    if (userPassword !== confirmPassword) {
      setPasswordMessage("Passwörter stimmen nicht überein.");
      setPasswordSuccess(false);
      return;
    }
    if (currentUser === "admin") {
      localStorage.setItem("admin_password", userPassword);
      setPasswordMessage("Admin-Passwort erfolgreich geändert.");
    } else {
      localStorage.setItem("user_password", userPassword);
      setPasswordMessage("Passwort erfolgreich geändert.");
    }
    setPasswordSuccess(true);
    setUserPassword("");
    setConfirmPassword("");
  };

  const getUsernameById = (id) => {
    const user = users.find(u => u.id === id);
    return user ? user.username : `#${id}`;
  };

  useEffect(() => {
    if (loggedIn) {
      fetchProducts();
      fetchTransactions();
      fetchUsers();
    }
  }, [loggedIn]);

  if (!loggedIn) return <Login setLoggedIn={setLoggedIn} setView={setView} />;

  return (
    <div className="grid gap-4 p-4">
      <div className="nav-bar">
        <button onClick={() => setView("products")}>Produkte</button>
        <button onClick={() => setView("transactions")}>Transaktionen</button>
        <button onClick={() => setView("users")}>Benutzer</button>
        <button onClick={() => setView("settings")}>Einstellungen</button>
        <button onClick={() => { localStorage.removeItem("loggedIn"); localStorage.removeItem("currentUser"); setLoggedIn(false); }}>Logout</button>
      </div>

      {view === "settings" && (
        <div className="section">
          <h1 className="text-2xl font-bold mb-4">Einstellungen</h1>
          <div className="grid gap-2 max-w-md">
            <input type="password" placeholder="Neues Passwort" className="p-2 border rounded" value={userPassword} onChange={(e) => setUserPassword(e.target.value)} />
            <input type="password" placeholder="Passwort bestätigen" className="p-2 border rounded" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
            <button onClick={changePassword}>Passwort ändern</button>
            {passwordMessage && <div className={`mt-2 ${passwordSuccess ? "text-green-600" : "text-red-500"}`}>{passwordMessage}</div>}
          </div>
          <div className="flex items-center gap-2">
            <input type="checkbox" checked={useVFL} onChange={toggleVfl} />
            <label className="ml-2">Vereinsflieger Integration aktivieren</label>
          </div>
        </div>
      )}

      {view === "products" && (
        <>
          <div className="section">
            <h1 className="text-2xl font-bold">Produktverwaltung</h1>
            {useVFL && (<button onClick={syncProducts}>Produkte von Vereinsflieger laden</button>)}
            <div className="p-4 grid grid-cols-3 gap-2">
              <input placeholder="Produktname" value={name} onChange={e => setName(e.target.value)} />
              <input placeholder="VFL Artikel-ID" value={vflArticleId} onChange={e => setVflArticleId(e.target.value.replace(/\D/g, ""))}/>
              <input placeholder="Preis € " type="number" value={price} onChange={e => setPrice(e.target.value)} />
              <input placeholder="MwSt (%)" type="number" step="0.1" value={salestax} onChange={e => setSalestax(e.target.value)} />
              <select value={category} onChange={e => setCategory(e.target.value)}>
                <option value="">Kategorie wählen</option>
                <option value="Getränke">Getränke</option>
                <option value="Snacks">Snacks</option>
                <option value="Eis">Eis</option>
              </select>
              <button onClick={addProduct}>Produkt hinzufügen</button>
            </div>
          </div>

          <div className="section">
            <div className="p-4">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>VFL Artikel-ID</th>
                    <th>Name</th>
                    <th>Preis</th>
                    <th>MWSt</th>
                    <th>Kategorie</th>
                    <th>Bearbeiten / Löschen</th>
                  </tr>
                </thead>
                <tbody>
                  {products.map(prod => (
                    <tr key={prod.id}>
                      <td>{prod.id}</td>
                      <td>{prod.vfl_articleid || "-"}</td>
                      <td>{prod.name}</td>
                      <td>{prod.price.toFixed(2)} €</td>
                      <td>{prod.salestax ? prod.salestax.toFixed(1) + " %" : "-"}</td>
                      <td>{prod.category}</td>
                      <td>
                      <div className="button-group">
                        <button onClick={() => startEditProduct(prod)} className="bg-yellow-400 px-2 py-1 rounded">Bearbeiten</button>
                        <button onClick={() => deleteProduct(prod.id)} className="bg-red-500 text-white px-2 py-1 rounded">Löschen</button>
                      </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {editingProduct && (
          <div className="modal-overlay">
            <div className="modal-content">
            <h3 className="text-xl font-semibold mb-4 text-center">Produkt bearbeiten</h3>
            <div className="grid gap-2">
              <input
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="p-2 border rounded"
              />
              <input
                placeholder="VFL Artikel-ID"
                value={editVflArticleId}
                onChange={(e) => setEditVflArticleId(e.target.value)}
              />
              <input
                value={editPrice}
                onChange={(e) => setEditPrice(e.target.value)}
                className="p-2 border rounded"
              />
              <input
                placeholder="MwSt (%)"
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={editSalestax}
                onChange={(e) => setEditSalestax(e.target.value)}
              />
              <select
                value={editCategory}
                onChange={(e) => setEditCategory(e.target.value)}
                className="p-2 border rounded"
              >
                <option value="">Kategorie wählen</option>
                <option value="Getränke">Getränke</option>
                <option value="Snacks">Snacks</option>
                <option value="Eis">Eis</option>
              </select>
              <div className="modal-buttons">
                <button onClick={saveProductEdit}>Speichern</button>
                <button onClick={() => setEditingProduct(null)}>Abbrechen</button>
              </div>
            </div>
          </div>
        </div>
      )}
      {view === "transactions" && (
        <>
          <div className="grid gap-4 p-4">
            <UtcClock />
          </div>
          <div className="section">
            <div className="flex justify-between items-center">
              <h1 className="text-2xl font-bold">Transaktionen</h1>
              <button onClick={exportTransactions}>CSV exportieren</button>
              <div className="flex items-center gap-6 mb-4">
              <label htmlFor="month" className="font-semibold">Monat wählen:</label>
              <input
                id="month"
                type="month"
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(e.target.value)}
                className="p-2 border rounded"
              />
            </div>
            </div>
            <div className="p-4">
              <table>
                <thead>
                  <tr>
                    <th>Transaktion-ID</th>
                    <th>Benutzer-ID</th>
                    <th>Produkte</th>
                    <th>Summe</th>
                    <th>Zeitpunkt</th>
                  </tr>
                </thead>
                <tbody>
                  {Array.isArray(filteredTransactions) && filteredTransactions.map(t => (
                    <tr key={t.id}>
                      <td>{t.id}</td>
                      <td>{getUsernameById(t.user_id)}</td>
                      <td>{t.items.map(i => `${i.product_name} (€${i.price.toFixed(2)})`).join(", ")}</td>
                      <td>{t.total.toFixed(2)} €</td>
                      <td>{new Date(t.timestamp).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {view === "users" && (
        <>
          <div className="section">
            <h1 className="text-2xl font-bold">Benutzerverwaltung</h1>{useVFL && (<button onClick={importUsers}>Mitglieder importieren (Vereinsflieger)</button>)}
            <div className="p-4 grid grid-cols-4 gap-2">
              <input placeholder="Benutzername" value={username} onChange={e => setUsername(e.target.value)} />
              <input placeholder="RFID" value={rfid} onChange={e => setRfid(e.target.value)} />
              <input placeholder="Mitgliedsnummer" value={vfMemberid} onChange={e => setVfMemberid(e.target.value)} />
              <input placeholder="Passwort" type="password" value={userPassword} onChange={e => setUserPassword(e.target.value)} />
              <button onClick={addUser}>Benutzer hinzufügen</button>
            </div>
          </div>

          <div className="section">
            <div className="p-4">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>RFID</th>
                    <th>Mitgliedsnummer</th>
                    <th>Bearbeiten / Löschen</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id}>
                      <td>{u.id}</td>
                      <td>{u.username}</td>
                      <td>{u.rfid}</td>
                      <td>{u.vf_memberid}</td>
                      <td>
                      <div className="button-group">
                        <button onClick={() => startEditUser(u)} className="bg-yellow-400 px-2 py-1 rounded">Bearbeiten</button>
                        <button onClick={() => deleteUser(u.id)} className="bg-red-500 text-white px-2 py-1 rounded">Löschen</button>
                      </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
      {editingUser && (
        <div className="modal-overlay">
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-xl font-semibold mb-4 text-center">Benutzer bearbeiten</h3>
            <div className="grid gap-2">
              <input className="p-2 border rounded" placeholder="Benutzername" value={editUsername} onChange={(e) => setEditUsername(e.target.value)} />
              <input className="p-2 border rounded" placeholder="RFID" value={editRfid} onChange={(e) => setEditRfid(e.target.value)} />
              <input className="p-2 border rounded" placeholder="Mitgliedsnummer" value={editVfMemberid} onChange={(e) => setEditVfMemberid(e.target.value)} />
              <input className="p-2 border rounded" type="password" placeholder="Neues Passwort" value={editPassword} onChange={(e) => setEditPassword(e.target.value)} />
              <div className="modal-buttons">
                <button onClick={saveUserEdit}>Speichern</button>
                <button onClick={() => setEditingUser(null)}>Abbrechen</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
  
}
