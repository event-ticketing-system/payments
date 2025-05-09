import React, { useEffect, useState } from 'react';

function App() {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8001/api/payments/pending")
      .then((res) => res.json())
      .then((data) => {
        console.log("Fetched payments:", data);
        setPayments(Array.isArray(data) ? data : []);  // ← Defensive check
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching payments:", err);
        setPayments([]); // Set empty array on failure
        setLoading(false);
      });
  }, []);

  const confirmPayment = (orderId) => {
    fetch(`http://localhost:8001/api/payments/confirm/${orderId}`, {
      method: "POST"
    })
      .then(res => res.json())
      .then(() => {
        setPayments(payments.filter(p => p.order_id !== orderId));
        alert("Payment confirmed!");
        window.location.href = "http://localhost:3001/";
      })
      .catch(err => {
        console.error(err);
        alert("Failed to confirm payment.");
      });
  };

  if (loading) return <p>Loading...</p>;

  return (
    <div style={{ padding: "2rem" }}>
      <h1>Pending Payments</h1>
      {payments.length === 0 ? (
        <p>No pending payments.</p>
      ) : (
        <table border="1" cellPadding="8" style={{ width: "100%" }}>
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Event</th>
              <th>Quantity</th>
              <th>Total</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {payments.map(payment => (
              <tr key={payment.order_id}>
                <td>{payment.order_id}</td>
                <td>{payment.event_name}</td>
                <td>{payment.quantity}</td>
                <td>${payment.total_price.toFixed(2)}</td>
                <td>{payment.payment_status}</td>
                <td>
                  <button onClick={() => confirmPayment(payment.order_id)}>Pay</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default App;
