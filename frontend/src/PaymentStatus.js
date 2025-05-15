// PaymentStatus.js
import React, { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import './PaymentStatus.css';

function useQuery() {
  return new URLSearchParams(useLocation().search);
}

const PaymentStatus = () => {
  const query = useQuery();
  const status = query.get("status");
  const [seconds, setSeconds] = useState(10);

  const redirectTo = "http://localhost:3001/api/catalog/events";

  useEffect(() => {
    const countdown = setInterval(() => {
      setSeconds((prev) => {
        if (prev === 1) {
          clearInterval(countdown);
          window.location.href = redirectTo;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(countdown);
  }, []);

  const renderContent = () => {
    switch (status) {
      case "success":
        return (
          <div className="status-box success">
            <h1>🎉 Payment Successful!</h1>
            <p>Your transaction was completed successfully.</p>
          </div>
        );
      case "pending":
        return (
          <div className="status-box pending">
            <h1>⏳ Payment Pending</h1>
            <p>Your payment is still being processed. Please wait.</p>
          </div>
        );
      case "error":
        return (
          <div className="status-box error">
            <h1>❌ Payment Failed</h1>
            <p>Something went wrong with your payment. Please try again later.</p>
          </div>
        );
      default:
        return (
          <div className="status-box unknown">
            <h1>🤔 Unknown Status</h1>
            <p>We're not sure what happened. Please contact support.</p>
          </div>
        );
    }
  };

  return (
    <div className="container">
      {renderContent()}
      <div className="redirect-msg">
        <p>Redirecting in <strong>{seconds}</strong> seconds...</p>
      </div>
    </div>
  );
};

export default PaymentStatus;
