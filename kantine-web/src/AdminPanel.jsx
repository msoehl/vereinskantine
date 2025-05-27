import { useEffect, useState } from "react";

function Login({ setLoggedIn }) {
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
  const [products, setProducts] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [users, setUsers] = useState([]);
  const [name, setName] = useState("");
  const [price, setPrice] = useState("");
  const [category, setCategory] = useState("");
  const [username, setUsername] = useState("");
  const [rfid, setRfid] = useState("");
  const [userPassword, setUserPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordMessage, setPasswordMessage] = useState("");
  const [passwordSuccess, setPasswordSuccess] = useState(false);

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

  const addProduct = async () => {
    await fetch("/products", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, price: parseFloat(price), category })
    });
    setName("");
    setPrice("");
    setCategory("");
    fetchProducts();
  };

  const addUser = async () => {
    await fetch("/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, rfid, password: userPassword })
    });
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

  useEffect(() => {
    if (loggedIn) {
      fetchProducts();
      fetchTransactions();
      fetchUsers();
    }
  }, [loggedIn]);

  if (!loggedIn) return <Login setLoggedIn={setLoggedIn} />;

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
        </div>
      )}

      {view === "products" && (
        <>
          <div className="section">
            <h1 className="text-2xl font-bold">Produktverwaltung</h1>
            <div className="p-4 grid grid-cols-3 gap-2">
              <input placeholder="Produktname" value={name} onChange={e => setName(e.target.value)} />
              <input placeholder="Preis" type="number" value={price} onChange={e => setPrice(e.target.value)} />
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
                    <th>Name</th>
                    <th>Preis</th>
                    <th>Kategorie</th>
                    <th>Löschen</th>
                  </tr>
                </thead>
                <tbody>
                  {products.map(prod => (
                    <tr key={prod.id}>
                      <td>{prod.id}</td>
                      <td>{prod.name}</td>
                      <td>{prod.price.toFixed(2)} €</td>
                      <td>{prod.category}</td>
                      <td><button onClick={() => deleteProduct(prod.id)}>Löschen</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
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
                  {Array.isArray(transactions) && transactions.map(t => (
                    <tr key={t.id}>
                      <td>{t.id}</td>
                      <td>{t.user_id}</td>
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
            <h1 className="text-2xl font-bold">Benutzerverwaltung</h1><button onClick={importUsers}>Mitglieder importieren (Vereinsflieger)</button>
            <div className="p-4 grid grid-cols-4 gap-2">
              <input placeholder="Benutzername" value={username} onChange={e => setUsername(e.target.value)} />
              <input placeholder="RFID" value={rfid} onChange={e => setRfid(e.target.value)} />
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
                    <th>Löschen</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id}>
                      <td>{u.id}</td>
                      <td>{u.username}</td>
                      <td>{u.rfid}</td>
                      <td><button onClick={() => deleteUser(u.id)}>Löschen</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
