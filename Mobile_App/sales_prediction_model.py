import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
import joblib
from datetime import datetime, timedelta

class SalesPredictionModel:
    def __init__(self, model_path=None):
        """Initialize the sales prediction model.
        
        Args:
            model_path: Path to a saved model file (optional).
        """
        if model_path:
            self.model = joblib.load(model_path)
            self.encoder = joblib.load(model_path.replace('.pkl', '_encoder.pkl'))
            self.trained = True
        else:
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.encoder = None
            self.trained = False
    
    def preprocess_data(self, data):
        """Preprocess sales data for training or prediction.
        
        Args:
            data: DataFrame with columns ['date', 'product_id', 'quantity', 'price', etc.]
        
        Returns:
            X: Feature matrix
            y: Target values (if available)
        """
        # Extract date features
        df = data.copy()
        df['date'] = pd.to_datetime(df['date'])
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        df['day'] = df['date'].dt.day
        df['hour'] = df['date'].dt.hour
        
        # Group by date and product to get daily sales
        daily_sales = df.groupby(['date', 'product_id']).agg({
            'quantity': 'sum',
            'price': 'mean',
            'day_of_week': 'first',
            'month': 'first',
            'day': 'first',
            'hour': 'first'
        }).reset_index()
        
        # One-hot encode categorical features
        categorical_features = ['product_id', 'day_of_week', 'month']
        
        if not self.trained:
            self.encoder = OneHotEncoder(sparse=False, handle_unknown='ignore')
            encoded_features = self.encoder.fit_transform(daily_sales[categorical_features])
        else:
            encoded_features = self.encoder.transform(daily_sales[categorical_features])
        
        encoded_df = pd.DataFrame(encoded_features, 
                                 columns=self.encoder.get_feature_names_out(categorical_features))
        
        # Combine encoded features with numerical features
        numerical_features = ['day', 'hour', 'price']
        X = pd.concat([encoded_df, daily_sales[numerical_features]], axis=1)
        
        if 'quantity' in daily_sales.columns:
            y = daily_sales['quantity']
            return X, y
        else:
            return X
    
    def train(self, training_data):
        """Train the model on historical sales data.
        
        Args:
            training_data: DataFrame with columns ['date', 'product_id', 'quantity', 'price', etc.]
        
        Returns:
            Training score
        """
        X, y = self.preprocess_data(training_data)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.model.fit(X_train, y_train)
        self.trained = True
        
        # Return score
        return self.model.score(X_test, y_test)
    
    def predict(self, features):
        """Predict sales based on features.
        
        Args:
            features: DataFrame with columns ['date', 'product_id', 'price', etc.]
        
        Returns:
            Predicted sales quantities
        """
        if not self.trained:
            raise ValueError("Model needs to be trained before making predictions")
        
        X = self.preprocess_data(features)
        return self.model.predict(X)
    
    def predict_future_sales(self, product_id, days_ahead=7, base_price=None, historical_data=None):
        """Predict future sales for a specific product.
        
        Args:
            product_id: The product identifier
            days_ahead: Number of days to predict
            base_price: Price to use for prediction (or use average if None)
            historical_data: Historical sales data to use for reference
        
        Returns:
            DataFrame with predicted sales for each future day
        """
        if not self.trained:
            raise ValueError("Model needs to be trained before making predictions")
        
        if historical_data is None or base_price is None:
            raise ValueError("Historical data and base price are required for prediction")
            
        # Filter data for this product
        product_data = historical_data[historical_data['product_id'] == product_id]
        
        # Use average price if base_price not provided
        if base_price is None:
            base_price = product_data['price'].mean()
        
        # Create future dates
        last_date = pd.to_datetime(historical_data['date']).max()
        future_dates = [last_date + timedelta(days=i+1) for i in range(days_ahead)]
        
        # Create prediction data
        future_data = []
        for date in future_dates:
            future_data.append({
                'date': date,
                'product_id': product_id,
                'price': base_price
            })
        
        future_df = pd.DataFrame(future_data)
        predictions = self.predict(future_df)
        
        # Create result dataframe
        result_df = pd.DataFrame({
            'date': future_dates,
            'product_id': product_id,
            'predicted_quantity': predictions,
            'price': base_price
        })
        
        return result_df
    
    def optimize_price(self, product_id, historical_data, price_range, cost_price):
        """Find optimal price for maximum profit.
        
        Args:
            product_id: The product identifier
            historical_data: Historical sales data
            price_range: Tuple of (min_price, max_price) to consider
            cost_price: Cost of the product
            
        Returns:
            Optimal price and predicted profit
        """
        min_price, max_price = price_range
        step = (max_price - min_price) / 20  # Test 20 different price points
        
        best_profit = -1
        optimal_price = min_price
        
        for price in np.arange(min_price, max_price + step, step):
            # Create test data with this price
            test_data = historical_data[historical_data['product_id'] == product_id].copy()
            test_data['price'] = price
            
            # Predict sales at this price
            predicted_qty = self.predict(test_data).sum()
            
            # Calculate profit
            profit = (price - cost_price) * predicted_qty
            
            if profit > best_profit:
                best_profit = profit
                optimal_price = price
        
        return optimal_price, best_profit
    
    def save(self, model_path):
        """Save the trained model to a file.
        
        Args:
            model_path: Path to save the model
        """
        if not self.trained:
            raise ValueError("Cannot save an untrained model")
        
        joblib.dump(self.model, model_path)
        joblib.dump(self.encoder, model_path.replace('.pkl', '_encoder.pkl'))
