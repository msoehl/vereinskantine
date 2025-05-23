import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

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
    <div className="grid gap-4 p-4">
      <h1 className="text-2xl font-bold">Login</h1>
      <Input placeholder="Benutzername" value={username} onChange={e => setUsername(e.target.value)} />
      <Input placeholder="Passwort" type="password" value={password} onChange={e => setPassword(e.target.value)} />
      <Button onClick={handleLogin}>Login</Button>
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
    <div className="grid gap-4 p-4">
      <div className="flex gap-4">
        <Button onClick={() => setView("products")}>Produkte</Button>
        <Button onClick={() => setView("transactions")}>Transaktionen</Button>
        <Button onClick={() => setView("users")}>Benutzer</Button>
      </div>

      {view === "products" && (
        <>
          <h1 className="text-2xl font-bold">Produktverwaltung</h1>
          <Card>
            <CardContent className="p-4 grid grid-cols-3 gap-2">
              <Input placeholder="Produktname" value={name} onChange={e => setName(e.target.value)} />
              <Input placeholder="Preis" type="number" value={price} onChange={e => setPrice(e.target.value)} />
              <Button onClick={addProduct}>Produkt hinzufügen</Button>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Preis</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {products.map(prod => (
                    <TableRow key={prod.id}>
                      <TableCell>{prod.id}</TableCell>
                      <TableCell>{prod.name}</TableCell>
                      <TableCell>{prod.price.toFixed(2)} €</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}

      {view === "transactions" && (
        <>
          <h1 className="text-2xl font-bold">Transaktionen</h1>
          <Card>
            <CardContent className="p-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Benutzer</TableHead>
                    <TableHead>Produkt</TableHead>
                    <TableHead>Zeit</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {transactions.map(t => (
                    <TableRow key={t.id}>
                      <TableCell>{t.id}</TableCell>
                      <TableCell>{t.user_id}</TableCell>
                      <TableCell>{t.product_id}</TableCell>
                      <TableCell>{new Date(t.timestamp).toLocaleString()}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}

      {view === "users" && (
        <>
          <h1 className="text-2xl font-bold">Benutzerverwaltung</h1>
          <Card>
            <CardContent className="p-4 grid grid-cols-4 gap-2">
              <Input placeholder="Benutzername" value={username} onChange={e => setUsername(e.target.value)} />
              <Input placeholder="RFID" value={rfid} onChange={e => setRfid(e.target.value)} />
              <Input placeholder="Passwort" type="password" value={userPassword} onChange={e => setUserPassword(e.target.value)} />
              <Button onClick={addUser}>Benutzer hinzufügen</Button>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>RFID</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map(u => (
                    <TableRow key={u.id}>
                      <TableCell>{u.id}</TableCell>
                      <TableCell>{u.username}</TableCell>
                      <TableCell>{u.rfid}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}