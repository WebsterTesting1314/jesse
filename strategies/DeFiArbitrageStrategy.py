"""
DeFi Arbitrage Strategy
A comprehensive strategy that demonstrates decentralized arbitrage trading
with MEV protection, flash loans, and multi-chain support
"""

import asyncio
import os
import time
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
import json
import logging

import jesse.helpers as jh
from jesse.strategies import Strategy
from jesse.models import Order
from jesse import utils
from jesse.enums import sides

# Import our DeFi components
from jesse.services.defi_mempool_monitor import (
    initialize_mempool_monitor, MempoolMonitor, MEVOpportunity, MEVType
)
from jesse.services.web3_client import (
    get_web3_client, ChainId, Web3Client, wei_to_ether, ether_to_wei
)
from jesse.services.hft_arbitrage_detector import (
    initialize_arbitrage_detector, ArbitrageDetector, ArbitrageOpportunity, 
    ArbitrageType, get_arbitrage_opportunities
)
from jesse.services.hft_event_system import hft_event_bus, EventType, Event
from jesse.services.notifier import notify

logger = logging.getLogger(__name__)


class DeFiArbitrageStrategy(Strategy):
    """
    Advanced DeFi Arbitrage Strategy
    
    Features:
    - Multi-chain arbitrage detection (Ethereum, BSC, Polygon)
    - MEV protection with mempool monitoring
    - Flash loan integration for capital efficiency
    - Comprehensive risk management
    - Real-time performance tracking
    """
    
    def __init__(self):
        super().__init__()
        
        # Strategy configuration
        self.vars['chains'] = [ChainId.ETHEREUM, ChainId.BSC, ChainId.POLYGON]
        self.vars['min_profit_bps'] = 50  # 0.5% minimum profit
        self.vars['max_price_impact'] = 0.03  # 3% max price impact
        self.vars['max_slippage'] = 0.03  # 3% max slippage
        self.vars['min_liquidity_usd'] = 50000  # $50k minimum liquidity
        self.vars['max_position_size_usd'] = 100000  # $100k max position
        self.vars['daily_loss_limit_usd'] = 10000  # $10k daily loss limit
        self.vars['max_concurrent_trades'] = 5
        self.vars['max_gas_price_gwei'] = 300
        self.vars['use_flashbots'] = True
        self.vars['flash_loan_providers'] = ['aave', 'dydx', 'uniswapv3']
        self.vars['execution_timeout_seconds'] = 300  # 5 minutes
        self.vars['retry_attempts'] = 3
        
        # Service instances
        self.mempool_monitor: Optional[MempoolMonitor] = None
        self.arbitrage_detector: Optional[ArbitrageDetector] = None
        self.web3_clients: Dict[ChainId, Web3Client] = {}
        
        # Performance tracking
        self.vars['daily_pnl'] = Decimal('0')
        self.vars['total_trades'] = 0
        self.vars['successful_trades'] = 0
        self.vars['failed_trades'] = 0
        self.vars['total_gas_spent'] = Decimal('0')
        self.vars['active_trades'] = {}
        self.vars['last_report_time'] = time.time()
        
        # Risk management
        self.vars['emergency_stop'] = False
        self.vars['last_reset_date'] = None
        
        # Flash loan contracts
        self.flash_loan_contracts = {
            'aave': {
                ChainId.ETHEREUM: '0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9',
                ChainId.POLYGON: '0x8dFf5E27EA6b7AC08EbFdf9eB090F32ee9a30fcf'
            },
            'dydx': {
                ChainId.ETHEREUM: '0x1E0447b19BB6EcFdAe1e4AE1694b0C3659614e4e'
            },
            'uniswapv3': {
                ChainId.ETHEREUM: '0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45',
                ChainId.POLYGON: '0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45'
            }
        }
        
    def before(self):
        """Initialize services and connections before trading starts"""
        logger.info("Initializing DeFi Arbitrage Strategy...")
        
        # Reset daily metrics if needed
        self._reset_daily_metrics_if_needed()
        
        # Initialize services
        asyncio.create_task(self._initialize_services())
        
    async def _initialize_services(self):
        """Initialize all required services"""
        try:
            # Initialize mempool monitor using Alchemy API key from env
            alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
            if not alchemy_api_key:
                raise RuntimeError("ALCHEMY_API_KEY not set in environment")
            self.mempool_monitor = initialize_mempool_monitor(
                web3_provider=f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_api_key}",
                chain_id=1,
                monitor_interval=0.1
            )
            
            # Initialize arbitrage detector
            self.arbitrage_detector = initialize_arbitrage_detector(
                chains=self.vars['chains'],
                min_profit_bps=self.vars['min_profit_bps'],
                max_price_impact=self.vars['max_price_impact'],
                update_interval=0.1
            )
            
            # Initialize Web3 clients for each chain using env vars
            for chain in self.vars['chains']:
                private_key = os.getenv(f"PRIVATE_KEY_{chain.name}")
                api_key = os.getenv(f"API_KEY_{chain.name}")
                rpc_url = os.getenv(f"RPC_URL_{chain.name}", self._get_rpc_url(chain))
                if not private_key or not api_key:
                    raise RuntimeError(
                        f"Env vars PRIVATE_KEY_{chain.name} and API_KEY_{chain.name} must be set"
                    )
                self.web3_clients[chain] = get_web3_client(
                    chain_id=chain,
                    private_key=private_key,
                    custom_rpc_url=rpc_url,
                    api_key=api_key
                )
            
            # Start services
            await self.mempool_monitor.start()
            await self.arbitrage_detector.start()
            
            # Subscribe to events
            await self._subscribe_to_events()
            
            logger.info("DeFi services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            self.vars['emergency_stop'] = True
    
    def _get_rpc_url(self, chain: ChainId) -> str:
        """Get RPC URL for a specific chain"""
        # Fallback RPC URLs; can be overridden via RPC_URL_<CHAIN_NAME> env var
        rpc_urls = {
            ChainId.ETHEREUM: "https://eth-mainnet.g.alchemy.com/v2/",
            ChainId.BSC: "https://bsc-dataseed.binance.org/",
            ChainId.POLYGON: "https://polygon-rpc.com/"
        }
        return rpc_urls.get(chain, "")
    
    async def _subscribe_to_events(self):
        """Subscribe to relevant events"""
        # Subscribe to arbitrage opportunities
        await hft_event_bus.subscribe(
            EventType.ARBITRAGE_OPPORTUNITY,
            self._on_arbitrage_opportunity
        )
        
        # Subscribe to MEV opportunities from mempool
        await hft_event_bus.subscribe(
            EventType.MARKET_DATA_UPDATE,
            self._on_mempool_update
        )
    
    async def _on_arbitrage_opportunity(self, event: Event):
        """Handle detected arbitrage opportunities"""
        if self.vars['emergency_stop']:
            return
        
        try:
            data = event.data
            opportunity_id = data['opportunity_id']
            
            # Fetch full opportunity details
            opportunities = self.arbitrage_detector.get_active_opportunities(
                min_profit_bps=self.vars['min_profit_bps']
            )
            
            opportunity = next(
                (o for o in opportunities if o.id == opportunity_id), 
                None
            )
            
            if opportunity:
                await self._process_arbitrage_opportunity(opportunity)
                
        except Exception as e:
            logger.error(f"Error handling arbitrage opportunity: {e}")
    
    async def _on_mempool_update(self, event: Event):
        """Handle mempool updates for MEV protection"""
        try:
            data = event.data
            if data.get('type') == 'mempool_transaction':
                # Check if this transaction could affect our trades
                tx_type = data.get('tx_type')
                if tx_type in ['swap', 'flash_loan']:
                    # Analyze for potential MEV threats
                    await self._check_mev_threat(data)
                    
        except Exception as e:
            logger.error(f"Error handling mempool update: {e}")
    
    async def _process_arbitrage_opportunity(self, opportunity: ArbitrageOpportunity):
        """Process and potentially execute an arbitrage opportunity"""
        # Check if we're already executing this opportunity
        if opportunity.id in self.vars['active_trades']:
            return
        
        # Validate opportunity
        if not await self._validate_opportunity(opportunity):
            return
        
        # Check risk limits
        if not self._check_risk_limits(opportunity):
            return
        
        # Check mempool safety
        if not await self._check_mempool_safety(opportunity):
            logger.warning(f"Mempool not safe for opportunity {opportunity.id}")
            return
        
        # Execute arbitrage
        await self._execute_arbitrage(opportunity)
    
    async def _validate_opportunity(self, opportunity: ArbitrageOpportunity) -> bool:
        """Validate arbitrage opportunity"""
        try:
            # Check expiry
            if time.time() > opportunity.expiry_time:
                return False
            
            # Check minimum profit
            if opportunity.profit_bps < self.vars['min_profit_bps']:
                return False
            
            # Check price impact
            if opportunity.price_impact > self.vars['max_price_impact']:
                return False
            
            # Check risk score
            if opportunity.risk_score > 0.7:  # High risk threshold
                return False
            
            # Verify liquidity for each pool
            for pool in opportunity.pools:
                liquidity_usd = pool.liquidity_usd or self._estimate_liquidity_usd(pool)
                if liquidity_usd < self.vars['min_liquidity_usd']:
                    return False
            
            # Estimate current gas costs
            gas_price = self._get_current_gas_price(opportunity.chain_ids[0])
            if gas_price > self.vars['max_gas_price_gwei'] * 10**9:
                return False
            
            # Recalculate profit with current gas
            gas_cost_usd = self._calculate_gas_cost_usd(
                opportunity.gas_estimate, 
                gas_price,
                opportunity.chain_ids[0]
            )
            
            net_profit = float(opportunity.expected_profit) - gas_cost_usd
            if net_profit < 50:  # Minimum $50 profit
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating opportunity: {e}")
            return False
    
    def _check_risk_limits(self, opportunity: ArbitrageOpportunity) -> bool:
        """Check if opportunity meets risk management criteria"""
        # Check daily loss limit
        if self.vars['daily_pnl'] < -self.vars['daily_loss_limit_usd']:
            logger.warning("Daily loss limit reached")
            self.vars['emergency_stop'] = True
            return False
        
        # Check concurrent trades
        if len(self.vars['active_trades']) >= self.vars['max_concurrent_trades']:
            return False
        
        # Check position size
        position_size_usd = float(opportunity.input_amount)
        if position_size_usd > self.vars['max_position_size_usd']:
            return False
        
        return True
    
    async def _check_mempool_safety(self, opportunity: ArbitrageOpportunity) -> bool:
        """Check if mempool is safe for execution"""
        if not self.mempool_monitor:
            return True  # Proceed if monitor not available
        
        try:
            # Get current mempool stats
            stats = self.mempool_monitor.get_stats()
            
            # Check for suspicious activity
            pending_count = stats.get('pending_transactions', 0)
            if pending_count > 10000:  # High congestion
                return False
            
            # Check for sandwich attacks on similar tokens
            for pool in opportunity.pools:
                token0 = pool.token_pair.token0
                token1 = pool.token_pair.token1
                
                # Check if tokens are being targeted
                if self._is_token_under_attack(token0) or self._is_token_under_attack(token1):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking mempool safety: {e}")
            return True  # Proceed with caution
    
    def _is_token_under_attack(self, token_address: str) -> bool:
        """Check if a token is under MEV attack"""
        # This would check recent transactions targeting this token
        # Simplified for example
        return False
    
    async def _execute_arbitrage(self, opportunity: ArbitrageOpportunity):
        """Execute arbitrage opportunity"""
        trade_id = opportunity.id
        self.vars['active_trades'][trade_id] = {
            'opportunity': opportunity,
            'start_time': time.time(),
            'status': 'pending'
        }
        
        try:
            # Determine execution method
            if await self._should_use_flash_loan(opportunity):
                result = await self._execute_with_flash_loan(opportunity)
            else:
                result = await self._execute_direct(opportunity)
            
            # Update metrics
            if result['success']:
                self.vars['successful_trades'] += 1
                self.vars['daily_pnl'] += Decimal(str(result['profit']))
                self.vars['total_gas_spent'] += Decimal(str(result['gas_cost']))
                
                logger.info(
                    f"Arbitrage executed successfully! "
                    f"Profit: ${result['profit']:.2f}, "
                    f"Gas: ${result['gas_cost']:.2f}"
                )
                
                # Send notification for significant profits
                if result['profit'] > 100:
                    await notify(
                        f"Arbitrage Success: ${result['profit']:.2f} profit "
                        f"({opportunity.type.value} on {opportunity.chain_ids[0].name})"
                    )
            else:
                self.vars['failed_trades'] += 1
                logger.error(f"Arbitrage failed: {result.get('error')}")
        
        except Exception as e:
            logger.error(f"Error executing arbitrage: {e}")
            self.vars['failed_trades'] += 1
        
        finally:
            # Clean up
            del self.vars['active_trades'][trade_id]
            self.vars['total_trades'] += 1
    
    async def _should_use_flash_loan(self, opportunity: ArbitrageOpportunity) -> bool:
        """Determine if flash loan should be used"""
        # Use flash loan for large trades or when capital is limited
        position_size = float(opportunity.input_amount)
        
        # Check available balance
        chain = opportunity.chain_ids[0]
        if chain in self.web3_clients:
            balance = self.web3_clients[chain].get_balance_in_ether(
                self.web3_clients[chain].account.address
            )
            
            # Use flash loan if insufficient balance
            if float(balance) < position_size * 1.1:  # 10% buffer
                return True
        
        # Use flash loan for large positions
        return position_size > 10000  # $10k threshold
    
    async def _execute_with_flash_loan(self, opportunity: ArbitrageOpportunity) -> Dict:
        """Execute arbitrage using flash loan"""
        try:
            chain = opportunity.chain_ids[0]
            web3_client = self.web3_clients.get(chain)
            
            if not web3_client:
                return {'success': False, 'error': 'No Web3 client for chain'}
            
            # Select best flash loan provider
            provider = self._select_flash_loan_provider(chain, opportunity)
            if not provider:
                return {'success': False, 'error': 'No flash loan provider available'}
            
            # Build flash loan transaction
            tx_data = await self._build_flash_loan_transaction(
                provider, opportunity, web3_client
            )
            
            # Execute with retry logic
            for attempt in range(self.vars['retry_attempts']):
                try:
                    # Send transaction
                    result = await web3_client.send_transaction(
                        to=tx_data['to'],
                        data=tx_data['data'],
                        gas=tx_data['gas'],
                        gas_price=tx_data['gas_price'],
                        wait_for_confirmation=True,
                        confirmations=1
                    )
                    
                    if result['success']:
                        # Calculate actual profit
                        profit = self._calculate_actual_profit(result, opportunity)
                        gas_cost = self._calculate_gas_cost_usd(
                            result['gasUsed'], 
                            result['gasPrice'],
                            chain
                        )
                        
                        return {
                            'success': True,
                            'profit': profit,
                            'gas_cost': gas_cost,
                            'tx_hash': result['hash']
                        }
                    
                except Exception as e:
                    logger.error(f"Flash loan attempt {attempt + 1} failed: {e}")
                    if attempt < self.vars['retry_attempts'] - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            return {'success': False, 'error': 'All flash loan attempts failed'}
            
        except Exception as e:
            logger.error(f"Flash loan execution error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _execute_direct(self, opportunity: ArbitrageOpportunity) -> Dict:
        """Execute arbitrage directly without flash loan"""
        try:
            chain = opportunity.chain_ids[0]
            web3_client = self.web3_clients.get(chain)
            
            if not web3_client:
                return {'success': False, 'error': 'No Web3 client for chain'}
            
            # Build transaction sequence
            transactions = await self._build_arbitrage_transactions(
                opportunity, web3_client
            )
            
            # Execute transactions
            results = []
            total_gas_used = 0
            
            for tx in transactions:
                result = await web3_client.send_transaction(
                    to=tx['to'],
                    value=tx.get('value', 0),
                    data=tx['data'],
                    gas=tx['gas'],
                    gas_price=tx['gas_price'],
                    wait_for_confirmation=True
                )
                
                if not result['success']:
                    # Revert if any transaction fails
                    return {'success': False, 'error': f"Transaction failed: {result.get('error')}"}
                
                results.append(result)
                total_gas_used += result['gasUsed']
            
            # Calculate profit
            profit = self._calculate_actual_profit(results[-1], opportunity)
            gas_cost = self._calculate_gas_cost_usd(
                total_gas_used,
                results[0]['gasPrice'],
                chain
            )
            
            return {
                'success': True,
                'profit': profit - gas_cost,
                'gas_cost': gas_cost,
                'tx_hashes': [r['hash'] for r in results]
            }
            
        except Exception as e:
            logger.error(f"Direct execution error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _select_flash_loan_provider(self, chain: ChainId, opportunity: ArbitrageOpportunity) -> Optional[str]:
        """Select best flash loan provider for the opportunity"""
        available_providers = []
        
        for provider in self.vars['flash_loan_providers']:
            if chain in self.flash_loan_contracts.get(provider, {}):
                available_providers.append(provider)
        
        if not available_providers:
            return None
        
        # Simple selection - in production, consider fees and availability
        return available_providers[0]
    
    async def _build_flash_loan_transaction(self, 
                                          provider: str,
                                          opportunity: ArbitrageOpportunity,
                                          web3_client: Web3Client) -> Dict:
        """Build flash loan transaction"""
        # This is a simplified example - actual implementation would be provider-specific
        flash_loan_address = self.flash_loan_contracts[provider][opportunity.chain_ids[0]]
        
        # Encode arbitrage logic as callback data
        arbitrage_data = self._encode_arbitrage_logic(opportunity)
        
        # Build transaction based on provider
        if provider == 'aave':
            # Aave V2 flash loan interface
            abi = [
                {
                    "name": "flashLoan",
                    "inputs": [
                        {"name": "receiverAddress", "type": "address"},
                        {"name": "assets", "type": "address[]"},
                        {"name": "amounts", "type": "uint256[]"},
                        {"name": "modes", "type": "uint256[]"},
                        {"name": "onBehalfOf", "type": "address"},
                        {"name": "params", "type": "bytes"},
                        {"name": "referralCode", "type": "uint16"}
                    ],
                    "outputs": [],
                    "type": "function"
                }
            ]
            
            # Prepare parameters
            assets = [opportunity.input_token]
            amounts = [int(opportunity.input_amount * 10**18)]  # Convert to wei
            modes = [0]  # No debt
            
            data = web3_client.encode_function_data(
                flash_loan_address,
                abi,
                "flashLoan",
                web3_client.account.address,  # receiver
                assets,
                amounts,
                modes,
                web3_client.account.address,  # onBehalfOf
                arbitrage_data,
                0  # referralCode
            )
            
        else:
            # Simplified for other providers
            data = b''
        
        # Estimate gas
        gas_estimate = opportunity.gas_estimate * 2  # Flash loans need more gas
        
        return {
            'to': flash_loan_address,
            'data': data,
            'gas': gas_estimate,
            'gas_price': web3_client.get_gas_price('fast')
        }
    
    async def _build_arbitrage_transactions(self,
                                          opportunity: ArbitrageOpportunity,
                                          web3_client: Web3Client) -> List[Dict]:
        """Build sequence of transactions for arbitrage"""
        transactions = []
        
        # Build transaction for each step in the arbitrage path
        for i, (token_from, token_to, dex) in enumerate(opportunity.path):
            pool = opportunity.pools[i]
            
            # Get DEX router address
            router_address = self._get_dex_router(dex, opportunity.chain_ids[0])
            
            # Calculate amounts with slippage
            input_amount = opportunity.input_amount if i == 0 else output_amount
            min_output = self._calculate_min_output(pool, input_amount)
            
            # Build swap transaction
            tx = await self._build_swap_transaction(
                web3_client,
                router_address,
                token_from,
                token_to,
                input_amount,
                min_output
            )
            
            transactions.append(tx)
            
            # Update output amount for next iteration
            output_amount = min_output
        
        return transactions
    
    def _encode_arbitrage_logic(self, opportunity: ArbitrageOpportunity) -> bytes:
        """Encode arbitrage execution logic for flash loan callback"""
        # This would encode the full arbitrage path and parameters
        # Simplified for example
        return b''
    
    def _get_dex_router(self, dex: Any, chain: ChainId) -> str:
        """Get DEX router address"""
        # Map of DEX routers by chain
        routers = {
            ChainId.ETHEREUM: {
                'uniswap_v2': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
                'sushiswap': '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F',
            },
            ChainId.BSC: {
                'pancakeswap': '0x10ED43C718714eb63d5aA57B78B54704E256024E',
            },
            ChainId.POLYGON: {
                'quickswap': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
            }
        }
        
        return routers.get(chain, {}).get(dex.value, '0x0000000000000000000000000000000000000000')
    
    async def _build_swap_transaction(self,
                                    web3_client: Web3Client,
                                    router_address: str,
                                    token_from: str,
                                    token_to: str,
                                    input_amount: Decimal,
                                    min_output: Decimal) -> Dict:
        """Build a swap transaction"""
        # Simplified swap interface
        swap_abi = [
            {
                "name": "swapExactTokensForTokens",
                "inputs": [
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "amountOutMin", "type": "uint256"},
                    {"name": "path", "type": "address[]"},
                    {"name": "to", "type": "address"},
                    {"name": "deadline", "type": "uint256"}
                ],
                "outputs": [{"name": "amounts", "type": "uint256[]"}],
                "type": "function"
            }
        ]
        
        # Prepare parameters
        amount_in = int(input_amount * 10**18)
        amount_out_min = int(min_output * 10**18)
        path = [token_from, token_to]
        deadline = int(time.time()) + 300  # 5 minutes
        
        data = web3_client.encode_function_data(
            router_address,
            swap_abi,
            "swapExactTokensForTokens",
            amount_in,
            amount_out_min,
            path,
            web3_client.account.address,
            deadline
        )
        
        return {
            'to': router_address,
            'data': data,
            'gas': 200000,  # Estimated
            'gas_price': web3_client.get_gas_price('fast')
        }
    
    def _calculate_min_output(self, pool: Any, input_amount: Decimal) -> Decimal:
        """Calculate minimum output with slippage"""
        # Calculate expected output
        expected_output = self._calculate_output_amount(pool, input_amount)
        
        # Apply slippage tolerance
        min_output = expected_output * (1 - Decimal(str(self.vars['max_slippage'])))
        
        return min_output
    
    def _calculate_output_amount(self, pool: Any, input_amount: Decimal) -> Decimal:
        """Calculate output amount for a swap"""
        # Simplified constant product formula
        # In production, use actual pool reserves and fees
        price = pool.get_price_0_to_1()
        fee = pool.fee / 10000  # Convert basis points to decimal
        
        output = input_amount * price * (1 - fee)
        return output
    
    def _estimate_liquidity_usd(self, pool: Any) -> Decimal:
        """Estimate pool liquidity in USD"""
        # Simplified estimation
        # In production, fetch token prices and calculate actual USD value
        return pool.reserve0 + pool.reserve1
    
    def _get_current_gas_price(self, chain: ChainId) -> int:
        """Get current gas price for a chain"""
        if chain in self.web3_clients:
            return self.web3_clients[chain].get_gas_price('fast')
        
        # Default gas prices by chain
        defaults = {
            ChainId.ETHEREUM: 30 * 10**9,
            ChainId.BSC: 5 * 10**9,
            ChainId.POLYGON: 30 * 10**9
        }
        return defaults.get(chain, 20 * 10**9)
    
    def _calculate_gas_cost_usd(self, gas_used: int, gas_price: int, chain: ChainId) -> float:
        """Calculate gas cost in USD"""
        # Native token prices (simplified - in production, fetch real prices)
        native_prices = {
            ChainId.ETHEREUM: 2000,  # ETH price
            ChainId.BSC: 300,        # BNB price
            ChainId.POLYGON: 1       # MATIC price
        }
        
        native_price = native_prices.get(chain, 1)
        gas_cost_native = wei_to_ether(gas_used * gas_price)
        
        return float(gas_cost_native) * native_price
    
    def _calculate_actual_profit(self, result: Dict, opportunity: ArbitrageOpportunity) -> float:
        """Calculate actual profit from execution result"""
        # In production, parse transaction logs to get actual amounts
        # Simplified to use expected profit
        return float(opportunity.expected_profit)
    
    async def _check_mev_threat(self, mempool_data: Dict):
        """Check for MEV threats in mempool"""
        # Check if transaction could sandwich our trades
        target_tokens = set()
        for trade_id, trade in self.vars['active_trades'].items():
            opp = trade['opportunity']
            for pool in opp.pools:
                target_tokens.add(pool.token_pair.token0)
                target_tokens.add(pool.token_pair.token1)
        
        # Simple check - in production, implement sophisticated analysis
        tx_to = mempool_data.get('to', '').lower()
        for token in target_tokens:
            if token.lower() in tx_to:
                logger.warning(f"Potential MEV threat detected for token {token}")
                # Could trigger protective actions here
    
    def _reset_daily_metrics_if_needed(self):
        """Reset daily metrics at start of new day"""
        current_date = jh.get_arrow().format('YYYY-MM-DD')
        
        if self.vars['last_reset_date'] != current_date:
            self.vars['daily_pnl'] = Decimal('0')
            self.vars['last_reset_date'] = current_date
            logger.info("Daily metrics reset")
    
    def should_long(self) -> bool:
        """Not used - strategy is event-driven"""
        return False
    
    def should_short(self) -> bool:
        """Not used - strategy is event-driven"""
        return False
    
    def go_long(self):
        """Not used - strategy is event-driven"""
        pass
    
    def go_short(self):
        """Not used - strategy is event-driven"""
        pass
    
    def on_open_position(self, order: Order):
        """Track when arbitrage execution completes"""
        logger.info(f"Arbitrage position opened: {order}")
    
    def should_cancel_entry(self) -> bool:
        """Check if we should cancel pending orders"""
        return self.vars['emergency_stop']
    
    def on_close_position(self, order: Order):
        """Handle position close"""
        logger.info(f"Arbitrage position closed: {order}")
    
    def terminate(self):
        """Clean up when strategy stops"""
        logger.info("Terminating DeFi Arbitrage Strategy...")
        
        # Stop services
        if self.mempool_monitor:
            asyncio.create_task(self.mempool_monitor.stop())
        
        if self.arbitrage_detector:
            asyncio.create_task(self.arbitrage_detector.stop())
        
        # Report final statistics
        self._report_statistics()
    
    def _report_statistics(self):
        """Report strategy performance statistics"""
        success_rate = (
            self.vars['successful_trades'] / max(self.vars['total_trades'], 1) * 100
        )
        
        logger.info(
            f"\nDeFi Arbitrage Strategy Statistics:\n"
            f"Total Trades: {self.vars['total_trades']}\n"
            f"Successful: {self.vars['successful_trades']}\n"
            f"Failed: {self.vars['failed_trades']}\n"
            f"Success Rate: {success_rate:.1f}%\n"
            f"Daily P&L: ${self.vars['daily_pnl']:.2f}\n"
            f"Total Gas Spent: ${self.vars['total_gas_spent']:.2f}\n"
            f"Active Trades: {len(self.vars['active_trades'])}"
        )
        
        # Send notification if significant profit
        if self.vars['daily_pnl'] > 1000:
            asyncio.create_task(notify(
                f"DeFi Arbitrage Daily Report: ${self.vars['daily_pnl']:.2f} profit!"
            ))
    
    async def run_periodic_tasks(self):
        """Run periodic maintenance tasks"""
        while True:
            try:
                # Report statistics every 5 minutes
                if time.time() - self.vars['last_report_time'] > 300:
                    self._report_statistics()
                    self.vars['last_report_time'] = time.time()
                
                # Check for stuck trades
                current_time = time.time()
                for trade_id, trade in list(self.vars['active_trades'].items()):
                    if current_time - trade['start_time'] > self.vars['execution_timeout_seconds']:
                        logger.warning(f"Trade {trade_id} timed out")
                        del self.vars['active_trades'][trade_id]
                
                await asyncio.sleep(30)  # Run every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in periodic tasks: {e}")
    
    @property
    def hyperparameters(self):
        """Define strategy hyperparameters for optimization"""
        return [
            {'name': 'min_profit_bps', 'type': int, 'min': 10, 'max': 200, 'default': 50},
            {'name': 'max_price_impact', 'type': float, 'min': 0.01, 'max': 0.1, 'default': 0.03},
            {'name': 'max_slippage', 'type': float, 'min': 0.01, 'max': 0.1, 'default': 0.03},
            {'name': 'min_liquidity_usd', 'type': int, 'min': 10000, 'max': 500000, 'default': 50000},
            {'name': 'max_position_size_usd', 'type': int, 'min': 1000, 'max': 1000000, 'default': 100000},
            {'name': 'max_gas_price_gwei', 'type': int, 'min': 50, 'max': 1000, 'default': 300},
        ]