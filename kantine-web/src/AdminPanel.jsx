import { useEffect, useState } from "react";


function Login({ setLoggedIn }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = () => {
    if ((username === "admin" && password === "admin") ||
        (username === localStorage.getItem("username") && password === localStorage.getItem("user_password"))) 
        {
      localStorage.setItem("loggedIn", "true");
      setLoggedIn(true);
    } else {
      alert("Falsche Zugangsdaten");
    }
  };

  return (
    <div className="login-container">
    <div className="grid gap-4 p-4">
      <h1 className="text-2xl font-bold">Login</h1>
      <input className="p-2 border rounded" placeholder="Benutzername" value={username} onChange={e => setUsername(e.target.value)} />
      <input className="p-2 border rounded" placeholder="Passwort" type="password" value={password} onChange={e => setPassword(e.target.value)} />
      <button onClick={handleLogin}>Login</button>
    </div>
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

  const deleteProduct = async (id) => {
  await fetch(`http://localhost:8000/products/${id}`, { method: "DELETE" });
  fetchProducts();
};

const deleteUser = async (id) => {
  await fetch(`http://localhost:8000/users/${id}`, { method: "DELETE" });
  fetchUsers();
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
      body: JSON.stringify({ name, price: parseFloat(price), category })
    });
    setName("");
    setPrice("");
    setCategory("");
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

  if (!loggedIn) return <Login setLoggedIn={setLoggedIn} />;

  return (
    
    <div className="grid gap-4 p-4">
      <div className="nav-bar">
      <div className="flex gap-4">
        <button onClick={() => setView("products")}>Produkte</button>
        <button onClick={() => setView("transactions")}>Transaktionen</button>
        <button onClick={() => setView("users")}>Benutzer</button>
        <button onClick={() => {localStorage.removeItem("loggedIn");setLoggedIn(false);}}>Logout</button>
      </div>
      </div>

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
                      <td><button onClick={() => deleteProduct(prod.id)}>Löschen</button></td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {view === "transactions" && (
        <>
          <div className="section">
            <h1 className="text-2xl font-bold">Transaktionen</h1>
            <div className="p-4">
              <table>
                <thead>
                  <tr>
                    <th>Benutzer</th>
                    <th>Product-ID</th>
                    <th>Produkt</th>
                    <th>Zeit</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map(t => (
                    <tr key={t.id}>
                      <td>{t.username}</td>
                      <td>{t.product_id}</td>
                      <td>{t.product_name}</td>
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
            <h1 className="text-2xl font-bold">Benutzerverwaltung</h1>
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
                      <td><button onClick={() => deleteUser(u.id)}>Löschen</button></td></tr>
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