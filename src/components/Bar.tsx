import React from 'react;

interface CarProps {
  make: string;
  model: string;
}

const Car: React.FC<CarProps> = ({ make, model }) => {
  return (
    <div style={{ border: '1px solid blue', padding: '10px', margin: '10px', backgroundColor: '#f0f0f0' }}>
      <h3>Car Details</h3>
      <p>Make: {make}</p>
      <p>Model: {model}</p>
    </div>
  );
};

interface BarProps {
  label: string;
  value: number;
}

const Bar: React.FC<BarProps> = ({ label, value }) => {
  const barWidth = (value / 100) * 200; // Scale for visual representation
  
  return (
    <div style={{ margin: '10px 0' }}>
      <div style={{ label: `${label}:`, display: 'inline-block', width: '100px', fontWeight: 'bold' }}>
        {label}
      </div>
      <div style={{ height: '20px', backgroundColor: '#eee', border: '1px solid #ccc', margin: '5px 0' }}>
        <div style={{ width: `${barWidth}%`, height: '100%', backgroundColor: 'green' }}></div>
      </div>
      <p>{value}%</p>
    </div>
  );
};

// Example usage (optional, for context)
const App: React.FC = () => {
  return (
    <div>
      <h1>Component Demo</h1>
      <Car make="Toyota" model="Camry" />
      <Bar label="Performance" value={85} />
      <Bar label="Efficiency" value={92} />
    </div>
  );
};

export { Car, Bar, App };
