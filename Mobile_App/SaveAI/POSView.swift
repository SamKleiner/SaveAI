//
//  POSView.swift
//  SaveAI
//
//  Created by Sam Kleiner on 3/1/25.
//
import SwiftUI

// POS Interface
struct POSView: View {
    @StateObject private var productsViewModel = ProductsViewModel()
    @StateObject private var saleViewModel = SaleViewModel()
    @StateObject private var storeStatusViewModel = StoreStatusViewModel()
    
    @State private var searchText = ""
    @State private var showingCheckout = false
    
    var filteredProducts: [Product] {
        productsViewModel.products.filter { product in
            searchText.isEmpty || product.name.localizedCaseInsensitiveContains(searchText)
        }
    }
    
    var body: some View {
        NavigationView {
            VStack {
                // Search Bar
                TextField("Search products", text: $searchText)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .padding()
                
                // Product List
                List(filteredProducts) { product in
                    HStack {
                        VStack(alignment: .leading) {
                            Text(product.name)
                                .font(.headline)
                            Text(product.formattedPrice)
                                .font(.subheadline)
                        }
                        Spacer()
                        Button(action: {
                            // For simplicity, add one unit at a time
                            saleViewModel.addToCart(product: product, quantity: 1)
                        }) {
                            Image(systemName: "plus.circle")
                                .font(.title2)
                        }
                    }
                }
                
                // Cart Summary
                if !saleViewModel.cartItems.isEmpty {
                    VStack(alignment: .leading) {
                        Text("Cart:")
                            .font(.headline)
                        List(saleViewModel.cartItems) { item in
                            HStack {
                                Text(item.productName)
                                Spacer()
                                Text("x\(item.quantity)")
                                Text(item.formattedTotal)
                            }
                        }
                        Button("Checkout") {
                            showingCheckout = true
                        }
                        .padding()
                        .sheet(isPresented: $showingCheckout) {
                            CheckoutView(saleViewModel: saleViewModel)
                        }
                    }
                    .padding()
                }
            }
            .navigationTitle("POS")
            .onAppear {
                productsViewModel.fetchProducts()
                saleViewModel.startNewSale()
            }
        }
    }
}
