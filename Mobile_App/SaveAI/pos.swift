//
//  pos.swift
//  SaveAI
//
//  Created by Sam Kleiner on 3/1/25.
//

import SwiftUI
import Combine

// MARK: - Data Models
struct Product: Identifiable, Hashable, Decodable {
    let id: Int
    let sku: String
    let name: String
    let description: String?
    let costPrice: Double
    let basePrice: Double
    var currentPrice: Double
    var stockQuantity: Int
    //var profitGroups: [ProfitGroup]
    
    var formattedPrice: String {
        String(format: "$%.2f", currentPrice)
    }
    
    var formattedCost: String {
        String(format: "$%.2f", costPrice)
    }
    
    var profit: Double {
        currentPrice - costPrice
    }
    
    var formattedProfit: String {
        String(format: "$%.2f", profit)
    }
    
    var profitPercentage: Double {
        (profit / costPrice) * 100
    }
    
    static func == (lhs: Product, rhs: Product) -> Bool {
        lhs.id == rhs.id
    }
    
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}

struct ProfitGroup: Identifiable, Decodable {
    let id: Int
    let name: String
    let minProfitPrice: Double
    var products: [Product] = []
    
    var formattedMinProfit: String {
        String(format: "$%.2f", minProfitPrice)
    }
}

struct SaleItem: Identifiable, Decodable {
    let id: Int
    let productId: Int
    let productName: String
    let quantity: Int
    let priceAtSale: Double
    
    var total: Double {
        Double(quantity) * priceAtSale
    }
    
    var formattedPrice: String {
        String(format: "$%.2f", priceAtSale)
    }
    
    var formattedTotal: String {
        String(format: "$%.2f", total)
    }
}

struct Sale: Identifiable, Decodable {
    let id: Int
    let customerId: Int?
    let totalAmount: Double
    let timestamp: Date
    var items: [SaleItem]
    
    var formattedTotal: String {
        String(format: "$%.2f", totalAmount)
    }
    
    var formattedDate: String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: timestamp)
    }
}

struct PricingRule: Identifiable, Decodable {
    let id: Int
    let productId: Int
    let ruleType: String
    let condition: String
    let discountPercentage: Double
    var isActive: Bool
}

struct SalesPrediction: Identifiable, Decodable {
    let id: UUID
    let date: Date
    let productId: Int
    let predictedQuantity: Double
    let price: Double
    
    var formattedDate: String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        return formatter.string(from: date)
    }
    
    var formattedQuantity: String {
        String(format: "%.1f", predictedQuantity)
    }
    
    enum CodingKeys: String, CodingKey {
        case date, productId, predictedQuantity, price
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.date = try container.decode(Date.self, forKey: .date)
        self.productId = try container.decode(Int.self, forKey: .productId)
        self.predictedQuantity = try container.decode(Double.self, forKey: .predictedQuantity)
        self.price = try container.decode(Double.self, forKey: .price)
        self.id = UUID() // Generate a new UUID during decoding
    }
}

// MARK: - API Service
class APIService {
    static let shared = APIService()
    private let baseURL = "http://localhost:8000"
    
    func fetchProducts(completion: @escaping ([Product]) -> Void) {
        guard let url = URL(string: "\(baseURL)/products/") else { return }
        
        URLSession.shared.dataTask(with: url) { data, response, error in
            guard let data = data else { return }
            
            do {
                let decoder = JSONDecoder()
                decoder.keyDecodingStrategy = .convertFromSnakeCase
                let dateFormatter = DateFormatter()
                dateFormatter.locale = Locale(identifier: "en_US_POSIX")
                dateFormatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"
                decoder.dateDecodingStrategy = .formatted(dateFormatter)
                let products = try decoder.decode([Product].self, from: data)
                DispatchQueue.main.async {
                    completion(products)
                }
            } catch {
                print("Error decoding products: \(error)")
            }
        }.resume()
    }
    
    func createProduct(name: String, sku: String, costPrice: Double, basePrice: Double,
                       stockQuantity: Int, description: String? = nil,
                       completion: @escaping (Product?) -> Void) {
        guard var components = URLComponents(string: "\(baseURL)/products/") else { return }
        
        var queryItems = [
            URLQueryItem(name: "name", value: name),
            URLQueryItem(name: "sku", value: sku),
            URLQueryItem(name: "cost_price", value: String(costPrice)),
            URLQueryItem(name: "base_price", value: String(basePrice)),
            URLQueryItem(name: "stock_quantity", value: String(stockQuantity))
        ]
        
        if let description = description {
            queryItems.append(URLQueryItem(name: "description", value: description))
        }
        
        components.queryItems = queryItems
        
        guard let url = components.url else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            guard let data = data else { return }
            
            do {
                let decoder = JSONDecoder()
                decoder.keyDecodingStrategy = .convertFromSnakeCase
                let dateFormatter = DateFormatter()
                dateFormatter.locale = Locale(identifier: "en_US_POSIX")
                dateFormatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"
                decoder.dateDecodingStrategy = .formatted(dateFormatter)
                let product = try decoder.decode(Product.self, from: data)
                DispatchQueue.main.async {
                    completion(product)
                }
            } catch {
                print("Error creating product: \(error)")
                completion(nil)
            }
        }.resume()
    }
    
    func updateStoreStatus(vacancyRate: Double?, lineLength: Int?, completion: @escaping (Bool) -> Void) {
        guard var components = URLComponents(string: "\(baseURL)/store-status/") else { return }
        
        var queryItems = [URLQueryItem]()
        
        if let vacancyRate = vacancyRate {
            queryItems.append(URLQueryItem(name: "vacancy_rate", value: String(vacancyRate)))
        }
        
        if let lineLength = lineLength {
            queryItems.append(URLQueryItem(name: "line_length", value: String(lineLength)))
        }
        
        components.queryItems = queryItems
        
        guard let url = components.url else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                completion(error == nil)
            }
        }.resume()
    }
    
    func createSale(customerId: Int? = nil, completion: @escaping (Sale?) -> Void) {
        guard var components = URLComponents(string: "\(baseURL)/sales/") else { return }
        
        if let customerId = customerId {
            components.queryItems = [URLQueryItem(name: "customer_id", value: String(customerId))]
        }
        
        guard let url = components.url else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            guard let data = data else { return }
            
            do {
                let decoder = JSONDecoder()
                decoder.keyDecodingStrategy = .convertFromSnakeCase
                let dateFormatter = DateFormatter()
                dateFormatter.locale = Locale(identifier: "en_US_POSIX")
                dateFormatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"
                decoder.dateDecodingStrategy = .formatted(dateFormatter)
                let sale = try decoder.decode(Sale.self, from: data)
                DispatchQueue.main.async {
                    completion(sale)
                }
            } catch {
                print("Error creating sale: \(error)")
                completion(nil)
            }
        }.resume()
    }
    
    func addItemToSale(saleId: Int, productId: Int, quantity: Int, completion: @escaping (Bool) -> Void) {
        guard var components = URLComponents(string: "\(baseURL)/sales/\(saleId)/add-item") else { return }
        
        components.queryItems = [
            URLQueryItem(name: "product_id", value: String(productId)),
            URLQueryItem(name: "quantity", value: String(quantity))
        ]
        
        guard let url = components.url else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                completion(error == nil)
            }
        }.resume()
    }
    
    func getSaleDetails(saleId: Int, completion: @escaping (Sale?) -> Void) {
        guard let url = URL(string: "\(baseURL)/sales/\(saleId)") else { return }
        
        URLSession.shared.dataTask(with: url) { data, response, error in
            guard let data = data else { return }
            
            do {
                let decoder = JSONDecoder()
                decoder.keyDecodingStrategy = .convertFromSnakeCase
                let dateFormatter = DateFormatter()
                dateFormatter.locale = Locale(identifier: "en_US_POSIX")
                dateFormatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"
                decoder.dateDecodingStrategy = .formatted(dateFormatter)
                let sale = try decoder.decode(Sale.self, from: data)
                DispatchQueue.main.async {
                    completion(sale)
                }
            } catch {
                print("Error fetching sale details: \(error)")
                completion(nil)
            }
        }.resume()
    }
    
    func fetchProfitGroups(completion: @escaping ([ProfitGroup]) -> Void) {
        guard let url = URL(string: "\(baseURL)/profit-groups/") else { return }
        
        URLSession.shared.dataTask(with: url) { data, response, error in
            guard let data = data else { return }
            
            do {
                let decoder = JSONDecoder()
                decoder.keyDecodingStrategy = .convertFromSnakeCase
                
                let dateFormatter = DateFormatter()
                dateFormatter.locale = Locale(identifier: "en_US_POSIX")
                dateFormatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"
                decoder.dateDecodingStrategy = .formatted(dateFormatter)
                
                let groups = try decoder.decode([ProfitGroup].self, from: data)
                DispatchQueue.main.async {
                    completion(groups)
                }
            } catch {
                print("Error decoding profit groups: \(error)")
            }
        }.resume()
    }
    
    func getForecast(productId: Int, days: Int = 7, completion: @escaping ([SalesPrediction]) -> Void) {
        guard let url = URL(string: "\(baseURL)/prediction/forecast/\(productId)?days=\(days)") else { return }
        
        URLSession.shared.dataTask(with: url) { data, response, error in
            guard let data = data else { return }
            
            do {
                let decoder = JSONDecoder()
                decoder.keyDecodingStrategy = .convertFromSnakeCase
                let dateFormatter = DateFormatter()
                dateFormatter.locale = Locale(identifier: "en_US_POSIX")
                dateFormatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"
                decoder.dateDecodingStrategy = .formatted(dateFormatter)
                let predictions = try decoder.decode([SalesPrediction].self, from: data)

                DispatchQueue.main.async {
                    completion(predictions)
                }
            } catch {
                print("Error decoding forecast: \(error)")
            }
        }.resume()
    }
    
    func getOptimalPrice(productId: Int, completion: @escaping ([String: Any]?) -> Void) {
        guard let url = URL(string: "\(baseURL)/prediction/optimal-price/\(productId)") else { return }
        
        URLSession.shared.dataTask(with: url) { data, response, error in
            guard let data = data else { return }
            
            do {
                if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                    DispatchQueue.main.async {
                        completion(json)
                    }
                }
            } catch {
                print("Error decoding optimal price: \(error)")
                completion(nil)
            }
        }.resume()
    }
}

// MARK: - View Models
class ProductsViewModel: ObservableObject {
    @Published var products: [Product] = []
    
    func fetchProducts() {
        APIService.shared.fetchProducts { [weak self] products in
            self?.products = products
        }
    }
    
    func addProduct(name: String, sku: String, costPrice: Double, basePrice: Double,
                    stockQuantity: Int, description: String? = nil) {
        APIService.shared.createProduct(
            name: name,
            sku: sku,
            costPrice: costPrice,
            basePrice: basePrice,
            stockQuantity: stockQuantity,
            description: description
        ) { [weak self] product in
            if let product = product {
                self?.products.append(product)
            }
        }
    }
}

class SaleViewModel: ObservableObject {
    @Published var currentSale: Sale?
    @Published var cartItems: [SaleItem] = []
    
    func startNewSale(customerId: Int? = nil) {
        APIService.shared.createSale(customerId: customerId) { [weak self] sale in
            self?.currentSale = sale
            self?.cartItems = []
        }
    }
    
    func addToCart(product: Product, quantity: Int) {
        guard let saleId = currentSale?.id else { return }
        
        APIService.shared.addItemToSale(saleId: saleId, productId: product.id, quantity: quantity) { [weak self] success in
            if success {
                // Refresh sale details
                self?.refreshSaleDetails()
            }
        }
    }
    
    func refreshSaleDetails() {
        guard let saleId = currentSale?.id else { return }
        
        APIService.shared.getSaleDetails(saleId: saleId) { [weak self] sale in
            if let sale = sale {
                self?.currentSale = sale
                self?.cartItems = sale.items
            }
        }
    }
    
    func completeSale() {
        // In a real app, we would process payment here
        startNewSale()
    }
}

class StoreStatusViewModel: ObservableObject {
    @Published var vacancyRate: Double = 0
    @Published var lineLength: Int = 0
    
    func updateStoreStatus() {
        APIService.shared.updateStoreStatus(vacancyRate: vacancyRate, lineLength: lineLength) { success in
            if success {
                print("Store status updated successfully")
            }
        }
    }
}

class PredictionViewModel: ObservableObject {
    @Published var predictions: [SalesPrediction] = []
    @Published var optimalPrice: Double?
    @Published var predictedProfit: Double?
    @Published var selectedProduct: Product?
    
    func getForecast(product: Product) {
        selectedProduct = product
        
        APIService.shared.getForecast(productId: product.id) { [weak self] predictions in
            self?.predictions = predictions
        }
    }
    
    func getOptimalPrice(product: Product) {
        selectedProduct = product
        
        APIService.shared.getOptimalPrice(productId: product.id) { [weak self] result in
            if let result = result {
                self?.optimalPrice = result["optimal_price"] as? Double
                self?.predictedProfit = result["predicted_profit"] as? Double
            }
        }
    }
}

// MARK: - App Entry Point
@main
struct POSFrontendApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
