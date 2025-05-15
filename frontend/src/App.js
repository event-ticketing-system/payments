import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import PaymentStatus from './PaymentStatus';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/payment/status" element={<PaymentStatus />} />
      </Routes>
    </Router>
  );
}

export default App;
