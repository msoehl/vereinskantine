import { useEffect, useState } from "react";

function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = () => {
    if ((username === "admin" && password === "admin") ||
        (username === localStorage.getItem("username") && password === localStorage.getItem("user_password"))) {
      onLogin();
    } else {
      alert("Falsche Zugangsdaten");
    }
  };

  return (
    <div style={{ padding: "1rem" }}>
      <h1>Login</h1>
      <input placeholder="Benutzername" value={username} onChange={e => setUsername(e.target.value)} />
      <input type="password" placeholder="Passwort" value={password} onChange={e => setPassword(e.target.value)} />
      <button onClick={handleLogin}>Login</button>
    </div>
  );
}

export default function AdminPanel() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [view, setView] = useState("products");
  const [products, setProducts] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [users, setUsers] = useState([]);
  const [name, setName] = useState("");
  const [price, setPrice] = useState("");
  const [username, setUsername] = useState("");
  const [rfid, setRfid] = useState("");
  const [userPassword, setUserPassword] = useState("");

  const fetchProducts = async () => {
    const res = await fetch("http://localhost:8000/products");
    const data = await res.json();
    setProducts(data);
  };

  const fetchTransactions = async () => {
    const res = await fetch("http://localhost:8000/transactions");
    const data = await res.json();
    setTransactions(data);
  };

  const fetchUsers = async () => {
    const res = await fetch("http://localhost:8000/users");
    const data = await res.json();
    setUsers(data);
  };

  const addProduct = async () => {
    await fetch("http://localhost:8000/products", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, price: parseFloat(price) })
    });
    setName("");
    setPrice("");
    fetchProducts();
  };

  const addUser = async () => {
    await fetch("http://localhost:8000/users", {
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

  useEffect(() => {
    if (loggedIn) {
      fetchProducts();
      fetchTransactions();
      fetchUsers();
    }
  }, [loggedIn]);

  if (!loggedIn) return <Login onLogin={() => setLoggedIn(true)} />;

  return (
    <div style={{ padding: "1rem" }}>
      <div>
        <button onClick={() => setView("products")}>Produkte</button>
        <button onClick={() => setView("transactions")}>Transaktionen</button>
        <button onClick={() => setView("users")}>Benutzer</button>
      </div>

      {view === "products" && (
        <>
          <h2>Produktverwaltung</h2>
          <input placeholder="Produktname" value={name} onChange={e => setName(e.target.value)} />
          <input type="number" placeholder="Preis" value={price} onChange={e => setPrice(e.target.value)} />
          <button onClick={addProduct}>Produkt hinzufügen</button>

          <table><thead><tr><th>ID</th><th>Name</th><th>Preis</th></tr></thead><tbody>
            {products.map(prod => (
              <tr key={prod.id}><td>{prod.id}</td><td>{prod.name}</td><td>{prod.price.toFixed(2)} €</td></tr>
            ))}
          </tbody></table>
        </>
      )}

      {view === "transactions" && (
        <>
          <h2>Transaktionen</h2>
          <table><thead><tr><th>ID</th><th>Benutzer</th><th>Produkt</th><th>Zeit</th></tr></thead><tbody>
            {transactions.map(t => (
              <tr key={t.id}><td>{t.id}</td><td>{t.user_id}</td><td>{t.product_id}</td><td>{new Date(t.timestamp).toLocaleString()}</td></tr>
            ))}
          </tbody></table>
        </>
      )}

      {view === "users" && (
        <>
          <h2>Benutzerverwaltung</h2>
          <input placeholder="Benutzername" value={username} onChange={e => setUsername(e.target.value)} />
          <input placeholder="RFID" value={rfid} onChange={e => setRfid(e.target.value)} />
          <input type="password" placeholder="Passwort" value={userPassword} onChange={e => setUserPassword(e.target.value)} />
          <button onClick={addUser}>Benutzer hinzufügen</button>

          <table><thead><tr><th>ID</th><th>Name</th><th>RFID</th></tr></thead><tbody>
            {users.map(u => (
              <tr key={u.id}><td>{u.id}</td><td>{u.username}</td><td>{u.rfid}</td></tr>
            ))}
          </tbody></table>
        </>
      )}
    </div>
  );
}
